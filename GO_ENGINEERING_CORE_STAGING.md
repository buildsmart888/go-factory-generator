# GO Engineering Core — source staging

The connected GitHub integration currently has no create-repository action.
The intended independent repository is **buildsmart888/go-engineering-core**;
it does **not yet exist**.

This branch stages the **exact v0.1 75-profile catalog snapshot** and its
solver-independent Python API under **go_engineering_core/**, separate from
GO Factory's existing plugin package. No change to production Core/Factory
runtime imports or public release is made here.

The complete repository-ready ZIP is delivered separately in this ChatGPT
conversation, including material/section contracts, Factory 01 portal fixture,
unit tests, documentation, pyproject and Apache-2.0 license.

Catalog version: 0.1.0
Catalog SHA-256: d69df97128b037313c97e51eae4c0a798eff00bcb721bbce6b0185aaabe8ff17

**Engineering caution:** 40 nominal geometries can compute approximate
2D A and inertias but remain UNVERIFIED. None of these is automatically a
verified 3D FEM property set. GO Structural Analysis 3D must use its existing
referenced A/Iy/Iz/J library or a separately verified manufacturer value set.

Once the user creates an empty GitHub repository, publish the repository-ready
source there. Keep a frozen offline catalog snapshot in each plugin with
the same version and SHA-256; never require a live network for offline use.
