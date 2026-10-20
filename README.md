# TinyML-Utilities

Ferramentas Python para **capturar vídeo de uma smartcamera TCP/LIMA**, com
imagens sem perdas e tempos de receção, e **extrair frames pela interface PyQt5**.

A captura grava Matroska (`.mkv`) com FFV1, à resolução nativa e com cadência
variável. Cada resposta válida origina um frame; não se duplicam nem descartam
frames para impor FPS constantes. Os indicadores aparecem apenas na janela.

Arduino, YOLO e anotação estão em [`legacy/`](legacy/README.md), para consulta,
fora da instalação ativa. Os vídeos antigos mantêm o seu formato.

## Instalação

É necessário Python 3.10 ou superior e ambiente gráfico para OpenCV/PyQt5.
Em PowerShell, na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Se já usas `venv/`, substitui `.venv` por `venv`. Após atualizar o repositório,
repete `pip install -e .` para instalar novas dependências. Também podes usar
`pip install -r requirements.txt`, que remete para a mesma instalação editável.

As dependências em `pyproject.toml` são PyAV, NumPy, OpenCV, Pillow e PyQt5.
No Windows validado, o wheel de PyAV inclui as bibliotecas necessárias à gravação;
não foi usado um executável `ffmpeg` separado. As dependências ainda não têm lock.

## Capturar

Liga o computador à rede da câmara e confirma IP e porta:

```powershell
.\.venv\Scripts\python.exe -m smartcamera.capture
.\.venv\Scripts\python.exe -m smartcamera.capture --ip 192.168.249.197 --port 33040 --fps 20
.\.venv\Scripts\python.exe -m smartcamera.capture --output data/videos/captures/ensaio_01.mkv
.\.venv\Scripts\python.exe -m smartcamera.capture --no-save
```

Por omissão, os destinos são gerados em `data/videos/captures/`:

| Ficheiro | Conteúdo |
| --- | --- |
| `capture_<data_hora>.mkv` | Vídeo FFV1 sem perdas, sem texto e à resolução nativa |
| `capture_<data_hora>.frames.csv` | Pedido, receção, timestamp relativo e tempos de processamento por frame |
| `capture_<data_hora>.session.json` | Configuração, estatísticas, estado final e motivo de paragem |

Um destino existente, incluindo os acompanhantes CSV/JSON, é recusado. Guarda
os três ficheiros juntos. `--no-save` mostra a captura sem criar nenhum deles.
Pressiona **q** na janela ou **Ctrl+C** no terminal para parar. Não há duração
programada nem reconexão automática.

`--fps` limita o ritmo alvo dos pedidos; **não determina a duração do vídeo**.
O instante zero é a primeira resposta completa recebida. O último frame permanece
até à paragem, incluindo eventual espera por uma resposta que falhou. Essa falha
fica identificada no JSON. Os tempos são do computador, não da exposição na câmara.

## Extrair frames

```powershell
.\.venv\Scripts\python.exe -m smartcamera.frame_grabber
.\.venv\Scripts\python.exe -m smartcamera.frame_grabber --videos-dir data/videos/20_10_2026 --frames-dir data/frames/ensaio_01
```

1. Escolhe um vídeo em **Open Video**. São aceites as capturas MKV e vídeos antigos.
2. Usa o slider ou **Previous Frame / Next Frame**.
3. Carrega em **Take Frame** para exportar a imagem visível.

O indicador usa o timestamp real do vídeo, incluindo cadência variável. A exportação
usa o frame já selecionado, à resolução original. **PNG preserva os píxeis**;
JPEG é uma opção com perdas. Redimensionar a janela não volta a ler o vídeo.
Se a abertura de outro vídeo falhar, o anterior continua disponível.

## Organização

```text
src/smartcamera/     Comunicação LIMA, gravação, captura e extrator
legacy/             Código e exemplos antigos, apenas para consulta
data/               Vídeos, frames, datasets, modelos e medições locais
tests/              Testes sem ligação à câmara; Qt offscreen
scripts/            Benchmark sintético, sem rede nem janela
docs/               Utilização, tempos, dados, migração e medições
pyproject.toml      Empacotamento e dependências ativas
```

Os dados locais, ambientes e resultados gerados ficam fora do Git. Todos os
caminhos relativos dependem da pasta atual do terminal; usa a raiz do projeto
para os destinos `data/` desta cópia, ou indica caminhos absolutos.

## Validação e documentação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/benchmark_capture.py --frames 100
```

O benchmark usa BMP sintético e timestamps simulados. Não mede o desempenho da
rede ou da câmara real. Os testes verificam píxeis, timestamps, duração, falhas
e exportação; o equipamento ainda precisa de um ensaio real.

- [Opções, protocolo, timestamps e metadados](docs/smartcamera.md)
- [Medições e respetivos limites](docs/performance.md)
- [Organização dos dados](docs/data-layout.md)
- [Migração inicial da organização](docs/migration.md)
- [Inventário do legado](legacy/README.md)

## Licença

[Unlicense](LICENSE).
