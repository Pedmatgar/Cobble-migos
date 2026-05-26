# Cobblemon Official Modpack [Fabric]

A Fabric modpack for Minecraft 1.21.1 built around [Cobblemon](https://modrinth.com/mod/cobblemon).

## Mod Sources

All mods in this pack are sourced from **[Modrinth](https://modrinth.com)** wherever possible.  
This applies to every mod tracked as a `.pw.toml` metadata file under `mods/`.

The one exception is `swingthrough-1.0.5+1.21.jar`, which is bundled directly in the repository because it is not available on Modrinth.

## World Generation

The pack includes two world-generation mods:

- **[Terralith](https://modrinth.com/mod/terralith)** – overhauled vanilla biomes and new biome types.
- **[Tectonic](https://modrinth.com/mod/tectonic)** – dramatically reshaped terrain generation.
  - Requires **[Lithostitched](https://modrinth.com/mod/lithostitched)** (bundled as a dependency).

## Pack Details

| Field | Value |
|---|---|
| Minecraft | 1.21.1 |
| Loader | Fabric 0.18.4 |
| Pack version | 1.7.3 |
| Author | Cobbled Studios |

## Building / Contributing

This pack uses [packwiz](https://packwiz.infra.link/). After editing any mod metadata, run:

```sh
packwiz refresh
```

to regenerate `index.toml`.
