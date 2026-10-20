# Dados locais

Esta pasta reúne os dados usados e gerados pelas ferramentas. Apenas este guia
é versionado; os outros conteúdos são ignorados pelo Git.

| Pasta | Conteúdo |
| --- | --- |
| `videos/` | Vídeos anteriormente guardados na raiz, com os nomes originais |
| `videos/20_10_2026/` | Gravações do grupo `20_10_2026` |
| `videos/examples/` | Vídeos anteriormente em `tests/videos/` |
| `videos/captures/` | Destino predefinido de novas capturas |
| `frames/` | Destino sugerido para imagens extraídas |
| `datasets/yolo/` | Datasets anteriormente em `tests/datasets/` |
| `datasets/positive_dataset/` | Amostras positivas históricas |
| `datasets/negative_dataset/` | Amostras negativas históricas |
| `models/` | Pesos e ficheiros auxiliares YOLO históricos |
| `runs/` | Resultados históricos de treino, preservando `detect/train*/` |
| `migration/` | Manifesto local da migração e cópias dos originais ativos |

As pastas sem dados podem não existir num clone novo. As ferramentas criam os
destinos necessários ao gravar. A migração não elimina nem deduplica ficheiros.

Consulta [a organização dos dados](../docs/data-layout.md) para os caminhos
antigos e novos. Os ficheiros ignorados não acompanham clones do repositório;
mantém cópias de segurança separadas dos dados que pretendes conservar.
