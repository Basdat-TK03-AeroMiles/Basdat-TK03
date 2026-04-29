CREATE SCHEMA aeromiles;

SET search_path TO aeromiles;

CREATE TABLE pengguna (
    email VARCHAR(100) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    salutation VARCHAR(10) NOT NULL,
    first_mid_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    tanggal_lahir DATE NOT NULL,
    kewarganegaraan VARCHAR(50) NOT NULL
);

CREATE TABLE tier (
    id_tier VARCHAR(10) PRIMARY KEY,
    nama VARCHAR(50) NOT NULL,
    minimal_frekuensi_terbang INT NOT NULL,
    minimal_tier_miles INT NOT NULL
);

CREATE TABLE penyedia (
    id SERIAL PRIMARY KEY
);

CREATE TABLE bandara (
    iata_code CHAR(3) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    kota VARCHAR(100) NOT NULL,
    negara VARCHAR(100) NOT NULL
);

CREATE TABLE award_miles_package (
    id VARCHAR(20) PRIMARY KEY,
    harga_paket DECIMAL(15,2) NOT NULL,
    jumlah_award_miles INT NOT NULL
);

CREATE TABLE member (
    email VARCHAR(100) PRIMARY KEY,
    nomor_member VARCHAR(20) UNIQUE NOT NULL,
    tanggal_bergabung DATE NOT NULL,
    id_tier VARCHAR(10) NOT NULL,
    award_miles INT,
    total_miles INT,
    FOREIGN KEY (email) REFERENCES pengguna(email),
    FOREIGN KEY (id_tier) REFERENCES tier(id_tier)
);

CREATE TABLE maskapai (
    kode_maskapai VARCHAR(10) PRIMARY KEY,
    nama_maskapai VARCHAR(100) NOT NULL,
    id_penyedia INT NOT NULL,
    FOREIGN KEY (id_penyedia) REFERENCES penyedia(id)
);

CREATE TABLE staf (
    email VARCHAR(100) PRIMARY KEY,
    id_staf VARCHAR(20) UNIQUE NOT NULL,
    kode_maskapai VARCHAR(10) NOT NULL,
    FOREIGN KEY (email) REFERENCES pengguna(email),
    FOREIGN KEY (kode_maskapai) REFERENCES maskapai(kode_maskapai)
);

CREATE TABLE mitra (
    email_mitra VARCHAR(100) PRIMARY KEY,
    id_penyedia INT UNIQUE NOT NULL,
    nama_mitra VARCHAR(100) NOT NULL,
    tanggal_kerja_sama DATE NOT NULL,
    FOREIGN KEY (id_penyedia) REFERENCES penyedia(id) ON DELETE CASCADE
);

CREATE TABLE identitas (
    nomor VARCHAR(50) PRIMARY KEY,
    email_member VARCHAR(100) NOT NULL,
    tanggal_habis DATE NOT NULL,
    tanggal_terbit DATE NOT NULL,
    negara_penerbit VARCHAR(50) NOT NULL,
    jenis VARCHAR(30) NOT NULL,
    FOREIGN KEY (email_member) REFERENCES member(email) ON DELETE CASCADE
);

CREATE TABLE member_award_miles_package (
    id_award_miles_package VARCHAR(20),
    email_member VARCHAR(100),
    timestamp TIMESTAMP,
    PRIMARY KEY (id_award_miles_package, email_member, timestamp),
    FOREIGN KEY (id_award_miles_package) REFERENCES award_miles_package(id),
    FOREIGN KEY (email_member) REFERENCES member(email) ON DELETE CASCADE
);

CREATE TABLE claim_missing_miles (
    id SERIAL PRIMARY KEY,
    email_member VARCHAR(100) NOT NULL,
    email_staf VARCHAR(100),
    maskapai VARCHAR(10) NOT NULL,
    bandara_asal CHAR(3) NOT NULL,
    bandara_tujuan CHAR(3) NOT NULL,
    tanggal_penerbangan DATE NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    nomor_tiket VARCHAR(20) NOT NULL,
    kelas_kabin VARCHAR(20) NOT NULL,
    pnr VARCHAR(10) NOT NULL,
    status_penerimaan VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (email_member) REFERENCES member(email) ON DELETE CASCADE,
    FOREIGN KEY (email_staf) REFERENCES staf(email),
    FOREIGN KEY (maskapai) REFERENCES maskapai(kode_maskapai),
    FOREIGN KEY (bandara_asal) REFERENCES bandara(iata_code),
    FOREIGN KEY (bandara_tujuan) REFERENCES bandara(iata_code),
    UNIQUE (email_member, flight_number, tanggal_penerbangan, nomor_tiket),
    CHECK (status_penerimaan IN ('Menunggu', 'Disetujui', 'Ditolak')),
    CHECK (kelas_kabin IN ('Economy', 'Business', 'First'))
);

CREATE TABLE transfer (
    email_member_1 VARCHAR(100) NOT NULL,
    email_member_2 VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    jumlah INT NOT NULL,
    catatan VARCHAR(255),
    PRIMARY KEY (email_member_1, email_member_2, timestamp),
    FOREIGN KEY (email_member_1) REFERENCES member(email) ON DELETE CASCADE,
    FOREIGN KEY (email_member_2) REFERENCES member(email) ON DELETE CASCADE,
    CHECK (email_member_1 <> email_member_2)
);

CREATE TABLE hadiah (
    kode_hadiah VARCHAR(20) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    miles INT NOT NULL,
    deskripsi TEXT,
    valid_start_date DATE NOT NULL,
    program_end DATE NOT NULL,
    id_penyedia INT NOT NULL,
    FOREIGN KEY (id_penyedia) REFERENCES penyedia(id) ON DELETE CASCADE
);

CREATE TABLE redeem (
    email_member VARCHAR(100) NOT NULL,
    kode_hadiah VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (email_member, kode_hadiah, timestamp),
    FOREIGN KEY (email_member) REFERENCES member(email) ON DELETE CASCADE,
    FOREIGN KEY (kode_hadiah) REFERENCES hadiah(kode_hadiah)
);



CREATE SEQUENCE member_seq START 1;


CREATE OR REPLACE FUNCTION generate_nomor_member() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.nomor_member IS NULL THEN
        NEW.nomor_member := 'M' || LPAD(nextval('member_seq')::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trigger_nomor_member
BEFORE INSERT ON member
FOR EACH ROW
EXECUTE FUNCTION generate_nomor_member();




CREATE SEQUENCE staf_seq START 1;



CREATE OR REPLACE FUNCTION generate_id_staf() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id_staf IS NULL THEN
        NEW.id_staf := 'S' || LPAD(nextval('staf_seq')::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trigger_id_staf
BEFORE INSERT ON staf
FOR EACH ROW
EXECUTE FUNCTION generate_id_staf();




CREATE SEQUENCE amp_seq START 1;



CREATE OR REPLACE FUNCTION generate_id_amp() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id IS NULL THEN
        NEW.id := 'AMP-' || LPAD(nextval('amp_seq')::TEXT, 3, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trigger_id_amp
BEFORE INSERT ON award_miles_package
FOR EACH ROW
EXECUTE FUNCTION generate_id_amp();



CREATE SEQUENCE hadiah_seq START 1;



CREATE OR REPLACE FUNCTION generate_kode_hadiah() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.kode_hadiah IS NULL THEN
        NEW.kode_hadiah := 'RWD-' || LPAD(nextval('hadiah_seq')::TEXT, 3, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE TRIGGER trigger_kode_hadiah
BEFORE INSERT ON hadiah
FOR EACH ROW
EXECUTE FUNCTION generate_kode_hadiah();