from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from utils.exceptions import Conflict


class ProgramPatchService:

    def _patch_collection(
        self,
        *,
        context,
        instance,
        items_data,
        deleted_ids,
        manager_name,
        model_cls,
        parent_fk_name,
        serializer_class,
        items_field_name,
        deleted_field_name,
    ):
        touched = False
        manager = getattr(instance, manager_name, None)
        if manager is None:
            raise NotImplementedError(f"Invalid manager_name: {manager_name}")

        if items_data is not None:
            for item in items_data:
                item_id = item.get("id")

                if item_id is None:
                    s = serializer_class(data=item, context=context)
                    try:
                        s.is_valid(raise_exception=True)
                    except serializers.ValidationError as e:
                        raise serializers.ValidationError({items_field_name: e.detail})

                    payload = dict(s.validated_data)
                    payload[parent_fk_name] = instance
                    model_cls.objects.create(**payload)
                    touched = True
                    continue

                obj = manager.filter(id=item_id).first()
                if obj is None:
                    raise serializers.ValidationError({
                        items_field_name: [f"{item_id} is not in this resource."]
                    })

                s = serializer_class(obj, data=item, partial=True, context=context)
                s.is_valid(raise_exception=True)
                s.save()
                touched = True

        if deleted_ids is not None:
            ids = set(deleted_ids)
            found = set(manager.filter(id__in=ids).values_list("id", flat=True))
            missing = ids - found
            if missing:
                raise serializers.ValidationError({
                    deleted_field_name: [f"Invalid ids: {sorted(missing)}"]
                })
            manager.filter(id__in=ids).delete()
            touched = True

        return touched

    def update(self, serializer, instance):
        validated_data = dict(serializer.validated_data)
        specs = serializer.get_collection_specs()
        context = serializer.context

        nested_map = {}
        deleted_map = {}
        for spec in specs:
            nested_map[spec.items_field_name] = validated_data.pop(spec.items_field_name, None)
            if spec.deleted_field_name:
                deleted_map[spec.deleted_field_name] = validated_data.pop(spec.deleted_field_name, None)

        client_version = serializer._get_client_version()
        now = timezone.now()
        version_field = serializer.get_version_field_name()
        model_cls = serializer.Meta.model

        with transaction.atomic():
            root_fields = serializer.get_root_update_fields(validated_data)

            file_fields = {}
            db_fields = {}
            for field_name, value in root_fields.items():
                try:
                    model_field = model_cls._meta.get_field(field_name)
                    if hasattr(model_field, 'upload_to'):
                        file_fields[field_name] = value
                        continue
                except Exception:
                    pass
                db_fields[field_name] = value

            db_fields[version_field] = now

            updated_rows = model_cls.objects.filter(
                pk=instance.pk,
                **{version_field: client_version},
            ).update(**db_fields)

            if updated_rows == 0:
                latest = serializer._get_latest_version(instance.pk)
                raise Conflict(server_updated_at=latest)

            instance = model_cls.objects.get(pk=instance.pk)

            if file_fields:
                for field_name, value in file_fields.items():
                    setattr(instance, field_name, value)
                instance.save(update_fields=list(file_fields.keys()))

            touched = False
            for spec in specs:
                items_data = nested_map.get(spec.items_field_name)
                deleted_ids = deleted_map.get(spec.deleted_field_name) if spec.deleted_field_name else None

                touched |= self._patch_collection(
                    context=context,
                    instance=instance,
                    items_data=items_data,
                    deleted_ids=deleted_ids,
                    manager_name=spec.manager_name,
                    model_cls=spec.model_cls,
                    parent_fk_name=spec.parent_fk_name,
                    serializer_class=spec.serializer_class,
                    items_field_name=spec.items_field_name,
                    deleted_field_name=spec.deleted_field_name or "",
                )

            if touched and serializer.should_bump_updated_at():
                model_cls.objects.filter(pk=instance.pk).update(**{version_field: timezone.now()})
                instance.refresh_from_db(fields=[version_field])

        return instance
