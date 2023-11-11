DROP TABLE IF EXISTS PersonaResistances, PersonaSkills, PersonaStats, Personas, Skills CASCADE;

CREATE TABLE Personas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    inherits VARCHAR(255) NOT NULL,
    item VARCHAR(255) NOT NULL,
    itemr VARCHAR(255) NOT NULL,
    lvl INT NOT NULL,
    trait VARCHAR(255) NOT NULL,
    arcana VARCHAR(255) NOT NULL
);

CREATE TABLE PersonaResistances (
    id SERIAL PRIMARY KEY,
    persona_id INT REFERENCES Personas(id) ON DELETE CASCADE,
    phys VARCHAR(1) NOT NULL,
    gun VARCHAR(1) NOT NULL,
    fire VARCHAR(1) NOT NULL,
    ice VARCHAR(1) NOT NULL,
    elec VARCHAR(1) NOT NULL,
    wind VARCHAR(1) NOT NULL,
    pys VARCHAR(1) NOT NULL,
    nuke VARCHAR(1) NOT NULL,
    bless VARCHAR(1) NOT NULL,
    curse VARCHAR(1) NOT NULL
);

CREATE TABLE PersonaSkills (
    id SERIAL PRIMARY KEY,
    persona_id INT REFERENCES Personas(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    level INT NOT NULL
);

CREATE TABLE PersonaStats (
    id SERIAL PRIMARY KEY,
    persona_id INT REFERENCES Personas(id) ON DELETE CASCADE,
    st INT NOT NULL,
    ma INT NOT NULL,
    en INT NOT NULL,
    ag INT NOT NULL,
    lu INT NOT NULL
);

CREATE TABLE Skills (
    id SERIAL PRIMARY KEY,
    element VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    cost INT NOT NULL,
    effect VARCHAR(255) NOT NULL,
    target VARCHAR(255) NOT NULL
);
