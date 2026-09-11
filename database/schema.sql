CREATE TABLE data_source (
    data_source_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name VARCHAR(200) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    source_date DATE
);

CREATE TABLE import_log (
    import_log_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data_source_id INTEGER NOT NULL,
    imported_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_loaded INTEGER DEFAULT 0,
    notes TEXT,

    CONSTRAINT fk_import_log_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source (data_source_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE excluded_party (
    party_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    party_type VARCHAR(20) NOT NULL,
    first_name VARCHAR(30),
    middle_name VARCHAR(100),
    last_name VARCHAR(30),
    business_name VARCHAR(255),
    provider_category VARCHAR(100),
    specialty VARCHAR(100),
    dob DATE,
    address VARCHAR(150),
    city VARCHAR(50),
    state VARCHAR(30),
    zip_code VARCHAR(10)
);

CREATE TABLE identifier (
    identifier_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    party_id INTEGER NOT NULL,
    identifier_type VARCHAR(10) NOT NULL,
    identifier_value VARCHAR(20) NOT NULL,

    CONSTRAINT fk_identifier_excluded_party
        FOREIGN KEY (party_id) REFERENCES excluded_party (party_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE exclusion_record (
    exclusion_record_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    party_id INTEGER NOT NULL,
    data_source_id INTEGER NOT NULL,
    import_log_id INTEGER NOT NULL,
    exclusion_type VARCHAR(50),
    exclusion_date DATE NOT NULL,
    reinstatement_date DATE,
    waiver_date DATE,
    waiver_state VARCHAR(10),
    status VARCHAR(20) DEFAULT 'ACTIVE',

    CONSTRAINT fk_exclusion_record_excluded_party
        FOREIGN KEY (party_id) REFERENCES excluded_party (party_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_exclusion_record_data_source
        FOREIGN KEY (data_source_id) REFERENCES data_source (data_source_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_exclusion_record_import_log
        FOREIGN KEY (import_log_id) REFERENCES import_log (import_log_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


CREATE INDEX idx_excluded_party_name
    ON excluded_party (last_name, first_name);

CREATE INDEX idx_excluded_party_business_name
    ON excluded_party (business_name);

CREATE INDEX idx_identifier_value
    ON identifier (identifier_value);
