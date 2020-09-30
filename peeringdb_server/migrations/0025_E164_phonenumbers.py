# Generated by Django 1.11.23 on 2019-12-12 08:46

import csv
import phonenumbers

from django.db import migrations
from django.conf import settings


def _edit_url(tag, instance):
    if tag == "poc":
        return f"{settings.BASE_URL}/net/{instance.network_id}/"
    else:
        return f"{settings.BASE_URL}/ix/{instance.id}/"


def _fix_number(tag, instance, field_name, list_fixed, list_invalid):
    number = getattr(instance, field_name, None).strip()
    if number:
        try:
            country = getattr(instance, "country", None)
            if country:
                country = country.code
            parsed_number = phonenumbers.parse(number, country)
            validated_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )

            if f"{validated_number}" == f"{number}":
                return

            setattr(instance, field_name, validated_number)
            list_fixed.append(
                [
                    tag,
                    instance.id,
                    _edit_url(tag, instance),
                    instance.status,
                    field_name,
                    number,
                    validated_number,
                    country,
                ]
            )
            print("FIXED", tag, instance.id, field_name, number, validated_number)
            instance.save()
        except Exception as exc:
            _push_invalid(tag, instance, field_name, number, list_invalid, f"{exc}")
            print("INVALID", tag, instance.id, field_name, number)


def _push_invalid(tag, instance, field_name, number, list_invalid, reason):
    country = getattr(instance, "country", None)
    if country:
        country = country.code
    list_invalid.append(
        [
            tag,
            instance.id,
            _edit_url(tag, instance),
            instance.status,
            field_name,
            number,
            country,
            reason.strip(),
        ]
    )


def forwards_func(apps, schema_editor):
    """
    Attempt to validate existing phone numbers to E164 format

    Output any that can't be validated to a invalid_phonenumbers.csv file
    Output any that were fixed to a fixed_phonenumbers.csv file
    """

    InternetExchange = apps.get_model("peeringdb_server", "InternetExchange")
    NetworkContact = apps.get_model("peeringdb_server", "NetworkContact")

    headers_invalid = [
        "type",
        "id",
        "status",
        "field",
        "phonenumber",
        "country",
        "reason",
    ]

    headers_fixed = [
        "type",
        "id",
        "status",
        "field",
        "phonenumber",
        "fixed",
        "country",
    ]

    invalid = []
    fixed = []

    for ix in InternetExchange.handleref.filter(status__in=["ok", "pending"]):
        _fix_number("ix", ix, "tech_phone", fixed, invalid)
        _fix_number("ix", ix, "policy_phone", fixed, invalid)

    for poc in NetworkContact.handleref.filter(status__in=["ok", "pending"]):
        _fix_number("poc", poc, "phone", fixed, invalid)

    print(
        "Invalid numbers: {} - written to invalid_phonenumbers.csv".format(len(invalid))
    )

    with open("invalid_phonenumbers.csv", "w+") as csvfile:
        csvwriter = csv.writer(csvfile, lineterminator="\n")
        csvwriter.writerow(headers_invalid)
        for row in invalid:
            csvwriter.writerow(row)

    print("Fixed numbers: {} - written to fixed_phonenumbers.csv".format(len(fixed)))

    with open("fixed_phonenumbers.csv", "w+") as csvfile:
        csvwriter = csv.writer(csvfile, lineterminator="\n")
        csvwriter.writerow(headers_fixed)
        for row in fixed:
            csvwriter.writerow(row)


class Migration(migrations.Migration):

    dependencies = [
        ("peeringdb_server", "0024_netixlan_asn"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
