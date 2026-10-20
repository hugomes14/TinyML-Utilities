# Organização dos dados

O código ativo está em `src/smartcamera/`; o código histórico está em `legacy/`.
Os dados de trabalho estão em `data/` e são ignorados pelo Git, exceto o seu
`README.md`. Não foi eliminado nem deduplicado nenhum vídeo, dataset ou modelo.

## Mapa de caminhos

| Origem | Destino |
| --- | --- |
| Vídeos `.mp4` e `.avi` na raiz | `data/videos/<nome original>` |
| `20_10_2026/` | `data/videos/20_10_2026/` |
| `tests/videos/` | `data/videos/examples/` |
| `tests/datasets/` | `data/datasets/yolo/` |
| `tests/positive_dataset/` | `data/datasets/positive_dataset/` |
| `tests/negative_dataset/` | `data/datasets/negative_dataset/` |
| `tests/modelos_yolo/` | `data/models/` |
| `runs/` | `data/runs/` |
| Novas gravações, por omissão | `data/videos/captures/` |
| Novos frames, pasta sugerida | `data/frames/` |

As subpastas históricas dos datasets e treinos mantêm os seus nomes. Por exemplo,
`runs/detect/train15/weights/best.pt` passa a
`data/runs/detect/train15/weights/best.pt`.

Os caminhos gravados **dentro** de ficheiros de configuração históricos, como
`data.yaml` e `args.yaml`, não foram reescritos. Os conteúdos foram preservados;
se recuperares um treino, terás de rever esses caminhos.

## Gravações futuras

Podes agrupar os novos ensaios em subpastas sem alterar a aplicação:

```powershell
python -m smartcamera.capture --output data/videos/captures/ensaio_01/camara.mp4
python -m smartcamera.frame_grabber --videos-dir data/videos/captures/ensaio_01 --frames-dir data/frames/ensaio_01
```

A captura cria as pastas necessárias ao gravar. O extrator cria as pastas do
destino escolhido ao exportar a imagem. Os caminhos são relativos ao terminal,
não à localização do módulo Python.

## Git e cópias locais

- `/data/*` exclui os dados locais e mantém apenas `/data/README.md` versionável.
- Vídeos e pesos também são ignorados por extensão se forem criados fora de `data/`.
- Ambientes virtuais, caches, resultados de testes e ficheiros de instalação são ignorados.
- Imagens, ficheiros `.txt`, `.cfg` e `.names` fora de `data/` podem ser versionados;
  deixam de existir exclusões globais que impediam documentação ou configuração.

Ignorar dados não constitui uma cópia de segurança. Um clone novo traz o código e
os guias; as pastas de dados são criadas quando necessárias. Para partilhar um
ensaio, transfere os ficheiros locais por um meio separado.
