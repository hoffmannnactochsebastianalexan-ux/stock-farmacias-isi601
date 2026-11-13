-- Esquema de la problemática (se usará completo en la Fase 3)
CREATE TABLE local (
    id          SERIAL PRIMARY KEY,
    nombre      TEXT NOT NULL,
    comuna      TEXT NOT NULL,
    direccion   TEXT NOT NULL
);

CREATE TABLE producto (
    id                SERIAL PRIMARY KEY,
    nombre            TEXT NOT NULL,
    principio_activo  TEXT NOT NULL,
    presentacion      TEXT NOT NULL
);

CREATE TABLE stock (
    local_id        INT NOT NULL REFERENCES local(id),
    producto_id     INT NOT NULL REFERENCES producto(id),
    cantidad        INT NOT NULL CHECK (cantidad >= 0),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (local_id, producto_id)
);

CREATE TABLE historial_stock (
    id           BIGSERIAL PRIMARY KEY,
    local_id     INT NOT NULL REFERENCES local(id),
    producto_id  INT NOT NULL REFERENCES producto(id),
    cantidad     INT NOT NULL,
    fecha        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Datos de ejemplo
INSERT INTO local (nombre, comuna, direccion) VALUES
  ('Farmacia Centro', 'Santiago', 'Ahumada 100'),
  ('Farmacia Providencia', 'Providencia', 'Av. Providencia 2000'),
  ('Farmacia Maipú', 'Maipú', 'Pajaritos 3000');

INSERT INTO producto (nombre, principio_activo, presentacion) VALUES
  ('Paracetamol 500 mg', 'paracetamol', '16 comprimidos'),
  ('Ibuprofeno 400 mg', 'ibuprofeno', '20 comprimidos'),
  ('Loratadina 10 mg', 'loratadina', '10 comprimidos');

INSERT INTO stock (local_id, producto_id, cantidad) VALUES
  (1, 1, 25), (1, 2, 10), (2, 1, 0), (2, 3, 7), (3, 2, 15), (3, 3, 3);
