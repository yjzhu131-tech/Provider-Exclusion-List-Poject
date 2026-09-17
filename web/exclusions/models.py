from django.db import models


class DataSource(models.Model):
    data_source_id = models.IntegerField(primary_key=True)
    source_name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20)
    source_date = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "data_source"
        ordering = ["source_name"]

    def __str__(self):
        return self.source_name


class ImportLog(models.Model):
    import_log_id = models.IntegerField(primary_key=True)
    data_source = models.ForeignKey(DataSource, models.DO_NOTHING, db_column="data_source_id")
    imported_at = models.DateTimeField()
    status = models.CharField(max_length=20)
    records_loaded = models.IntegerField(default=0)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "import_log"
        ordering = ["-imported_at"]


class ExcludedParty(models.Model):
    party_id = models.IntegerField(primary_key=True)
    party_type = models.CharField(max_length=20)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    business_name = models.CharField(max_length=255, null=True, blank=True)
    provider_category = models.CharField(max_length=100, null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=150, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=30, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "excluded_party"
        ordering = ["last_name", "first_name", "business_name"]

    @property
    def display_name(self):
        if self.business_name:
            return self.business_name
        return " ".join(part for part in [self.first_name, self.middle_name, self.last_name] if part)

    def __str__(self):
        return self.display_name or f"Party {self.party_id}"


class Identifier(models.Model):
    identifier_id = models.IntegerField(primary_key=True)
    party = models.ForeignKey(ExcludedParty, models.DO_NOTHING, db_column="party_id", related_name="identifiers")
    identifier_type = models.CharField(max_length=10)
    identifier_value = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = "identifier"

    def __str__(self):
        return f"{self.identifier_type}: {self.identifier_value}"


class ExclusionRecord(models.Model):
    exclusion_record_id = models.IntegerField(primary_key=True)
    party = models.ForeignKey(ExcludedParty, models.DO_NOTHING, db_column="party_id", related_name="exclusion_records")
    data_source = models.ForeignKey(DataSource, models.DO_NOTHING, db_column="data_source_id")
    import_log = models.ForeignKey(ImportLog, models.DO_NOTHING, db_column="import_log_id")
    exclusion_type = models.CharField(max_length=50, null=True, blank=True)
    exclusion_date = models.DateField()
    reinstatement_date = models.DateField(null=True, blank=True)
    waiver_date = models.DateField(null=True, blank=True)
    waiver_state = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=20, default="ACTIVE")

    class Meta:
        managed = False
        db_table = "exclusion_record"
        ordering = ["-exclusion_date"]
