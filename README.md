# TinyML-Utilities

Ferramentas Python para **capturar vídeo de uma smartcamera através de TCP/LIMA**
e **extrair frames de vídeos através de uma interface PyQt5**.

O código antigo de Arduino, YOLO e anotação está em [`legacy/`](legacy/README.md),
preservado apenas para consulta. Não faz parte da instalação ativa.

## Instalação

É necessário Python 3.10 ou superior e um ambiente gráfico para OpenCV/PyQt5.
A refatoração foi validada em Windows com Python 3.13. Os comandos seguintes são
para PowerShell, executados na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Se já tens o ambiente `venv/`, podes utilizá-lo substituindo `.venv` por `venv`.
Não é necessário ativar o ambiente quando usas o caminho completo do executável.
Como alternativa à instalação editável acima:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

As dependências ativas são declaradas em `pyproject.toml`: NumPy, OpenCV, Pillow
e PyQt5. Arduino CLI, pyserial, Matplotlib e Ultralytics pertencem ao legado e
não são instalados com estas ferramentas. As versões mínimas estão declaradas;
o projeto ainda não tem um ficheiro de lock.

## Capturar da smartcamera

Liga o computador à rede da câmara e confirma o IP e a porta na configuração do
equipamento. A predefinição atual é `192.168.249.197:33040`.

```powershell
.\.venv\Scripts\python.exe -m smartcamera.capture
.\.venv\Scripts\python.exe -m smartcamera.capture --ip 192.168.249.197 --port 33040 --fps 20
.\.venv\Scripts\python.exe -m smartcamera.capture --output data/videos/captures/ensaio_01.mp4
.\.venv\Scripts\python.exe -m smartcamera.capture --no-save
```

O primeiro comando mostra e grava a captura. Por omissão, gera um nome com data,
hora e microssegundos em `data/videos/captures/`. Um destino existente é recusado.
Pressiona **q** na janela para terminar; **Ctrl+C** no terminal também interrompe
a captura. A ligação e o gravador são fechados ao sair.

Os **20 FPS são um alvo**, usado também como FPS fixos do ficheiro. A relação
entre duração do vídeo e tempo real ainda depende do ritmo efetivo da câmara.
A lógica temporal foi mantida; a sua revisão fica para a fase de otimização.
Não há paragem automática por duração.

## Extrair frames

```powershell
.\.venv\Scripts\python.exe -m smartcamera.frame_grabber
.\.venv\Scripts\python.exe -m smartcamera.frame_grabber --videos-dir data/videos/20_10_2026 --frames-dir data/frames/ensaio_01
```

1. Carrega em **Open Video** e escolhe o vídeo.
2. Usa o slider ou **Previous Frame / Next Frame** para navegar.
3. Carrega em **Take Frame** e escolhe onde guardar a imagem em PNG ou JPEG.

A pasta sugerida é `data/frames/`; o nome inclui o vídeo de origem e o número do
frame. A imagem é exportada à resolução original, independentemente do tamanho
da janela. O diálogo de gravação permite escolher outro caminho.

## Organização

```text
src/smartcamera/     Captura LIMA e interface de extração de frames
legacy/             Código, exemplos e configuração antigos, para consulta
data/               Vídeos, frames, datasets, modelos e resultados locais
tests/              Testes automáticos sem ligação à câmara
docs/               Guias da smartcamera, dos dados e da migração
pyproject.toml      Metadados, empacotamento e dependências ativas
requirements.txt    Instalação editável a partir de pyproject.toml
```

Os dados ficam fora do Git. A documentação acompanha o repositório; ficheiros
`.txt`, imagens e configurações fora de `data/` já não são excluídos genericamente.
O ambiente virtual não é movido nem versionado.

Todos os caminhos relativos dos comandos são resolvidos a partir da **pasta
atual do terminal**. Executa-os na raiz do repositório para usar `data/` desta
cópia; fora dela, indica destinos absolutos ou os caminhos pretendidos.

## Documentação e validação

- [Ligação, opções, protocolo LIMA e limitações](docs/smartcamera.md)
- [Organização dos dados e mapa de caminhos](docs/data-layout.md)
- [Decisões e verificação da migração](docs/migration.md)
- [Inventário do legado](legacy/README.md)

```powershell
.\.venv\Scripts\python.exe -m smartcamera.capture --help
.\.venv\Scripts\python.exe -m smartcamera.frame_grabber --help
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam mensagens LIMA simuladas e vídeos temporários; não ligam à câmara.
A validação real do streaming exige o equipamento disponível na rede.

## Licença

[Unlicense](LICENSE).
