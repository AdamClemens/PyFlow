# Numerical Method Compatibility

Per `docs/planning/knowledge-architecture.md` KA-008.

Which numerical method families can be combined, and in what sense.
"Can be used together" means several different things -- interchangeable
implementations, methods coexisting at different layers, coupled methods,
hybrid approaches, and post-processing-only combinations are not the same
relationship, and this document should not collapse them into a single
compatibility label.

For the properties of each individual method, see `overview.md` (KA-007).

**Provenance:** split from the survey on 2026-08-15 when it moved from
`docs/planning/numerical-frameworks.md` into the handbook. Content is
unchanged apart from this header and the repair of an unbalanced code
fence around the classification tree below. See
`docs/CHANGELOG-DESIGN.md`.

**Status:** the pairwise graph and the "very common ... rare" grouping
below record observed practice. KA-008's Definition of Done additionally
requires the *kinds* of compatibility above to be distinguished
explicitly, and incompatibilities to be stated -- neither is done yet.
See `docs/planning/backlog.md`.

---

The following graph summarises common combinations found in practice.

```text
                    CFD Numerical Methods

                              ┌──────────────┐
                              │     FDM      │
                              └──────┬───────┘
                                     │
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
         ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
         │     FVM     │──────│     FEM     │──────│  Spectral   │
         └───┬────┬────┘      └─────────────┘      └─────────────┘
             │    │
             │    │
      ┌──────▼┐  ┌▼─────────┐
      │  LBM  │  │   SPH    │
      └───────┘  └────┬─────┘
                      │
              ┌───────▼────────┐
              │ PIC / FLIP     │
              └───────┬────────┘
                      │
                ┌─────▼─────┐
                │    MPM    │
                └───────────┘
```

### Interpretation

**Very common**

- FVM ↔ FEM
- FVM ↔ SPH
- SPH ↔ DEM (future handbook entry)
- FEM ↔ Structural Mechanics

**Common**

- FDM ↔ FVM
- FVM ↔ LBM
- FEM ↔ Spectral

**Occasional**

- SPH ↔ PIC/FLIP
- MPM ↔ FEM
- MPM ↔ SPH

**Rare**

- FDM ↔ SPH
- FDM ↔ PIC
- Spectral ↔ SPH

### Classification

```text
Field-based
├── FDM
├── FVM
├── FEM
└── Spectral

Particle-based
├── SPH
├── PIC
├── FLIP
└── MPM

Distribution-based
└── LBM
```
