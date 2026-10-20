# Smartcamera: utilização e protocolo

## Ferramentas ativas

- `smartcamera.capture`: ligação à câmara, pedidos BMP, visualização e gravação.
- `smartcamera.frame_grabber`: leitura de um vídeo local e exportação de frames.

Instala o projeto com `python -m pip install -e .`. Os exemplos abaixo pressupõem
o Python desse ambiente e o terminal aberto na raiz do repositório.

## Ligação e captura

O computador tem de alcançar a câmara por TCP. O IP predefinido é o usado no
código anterior; ajusta-o ao equipamento. O caminho LIMA corresponde à imagem
monocromática do projeto da câmara.

```powershell
python -m smartcamera.capture --ip 192.168.249.197 --port 33040 --fps 20
```

| Opção | Predefinição | Efeito |
| --- | --- | --- |
| `--ip` | `192.168.249.197` | IP ou hostname da câmara |
| `--port` | `33040` | Porta TCP, entre 1 e 65535 |
| `--fps` | `20` | FPS alvo e FPS fixos do vídeo; número finito positivo |
| `--output` | Nome gerado em `data/videos/captures/` | Novo ficheiro `.mp4`; cria as pastas necessárias e recusa ficheiros existentes |
| `--no-save` | Desativado | Mostra o streaming sem gravar; incompatível com `--output` |
| `--help` | — | Mostra a ajuda sem iniciar ligação ou abrir janelas |

O nome automático é `capture_AAAAMMDD_HHMMSS_microssegundos.mp4`, usando a hora
local do computador. Os caminhos relativos dependem da pasta atual do terminal.
A janela e o vídeo têm 960 × 720 pixels. Mantêm-se o redimensionamento por vizinho
mais próximo e os textos de FPS médios e tempo relativo sobre a imagem gravada.
O codec é `mp4v`.

Termina com **q** na janela ou **Ctrl+C** no terminal. A captura é contínua;
o nome do ficheiro não determina uma duração nem um temporizador.

## Sequência TCP/LIMA implementada

1. Abre um socket TCP com timeout de 5 segundos, `TCP_NODELAY` e um buffer de
   receção solicitado de 4 MiB.
2. Envia o pedido ASCII:

   ```xml
   <LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>
   ```

3. Lê o cabeçalho até `>`, com limite de 2048 bytes, e extrai `DATALEN`.
4. Recebe exatamente o número de bytes indicado, em blocos de até 262144 bytes.
5. Descodifica o BMP com OpenCV. Caso não seja descodificado, tenta Pillow e
   converte para BGR.
6. Mostra e, se solicitado, grava o frame. Repete o pedido ao ritmo alvo.

Esta descrição documenta o cliente existente. O comando e o caminho da imagem
dependem do projeto configurado na câmara; ainda não são opções da linha de
comandos. Não há reconexão automática.

## Utilização em Python

```python
from smartcamera.capture import SmartCameraStableFPS

camera = SmartCameraStableFPS(
    ip="192.168.249.197",
    port=33040,
    fps=20,
    output_path="data/videos/captures/ensaio_02.mp4",
)
camera.run()
```

Para apenas visualizar, usa `save_video=False`. `run()` fecha a ligação, as
janelas e o gravador ao terminar, incluindo erros durante a preparação da janela
ou da gravação. Criar a instância ou importar o módulo não liga à câmara.

## Extrator de frames

```powershell
python -m smartcamera.frame_grabber --videos-dir data/videos --frames-dir data/frames
```

As opções definem as pastas sugeridas pelos diálogos, que continuam a permitir
escolher outros caminhos. O vídeo é aberto por **Open Video**. O slider e os
botões navegam frame a frame; **Take Frame** relê o frame selecionado e exporta
a imagem original, sem o redimensionamento da pré-visualização.

O nome sugerido é `<video>_frame_<numero>.png`; a numeração visível começa em 1.
São aceites `.png`, `.jpg` e `.jpeg`, com PNG por omissão. A gravação usa
`cv2.imencode()` e `tofile()` para suportar caminhos Windows com acentos. A seleção
de um destino existente é tratada pelo diálogo de gravação da interface.

## Diagnóstico

| Sintoma | Verificação |
| --- | --- |
| `No module named smartcamera` | Usar o Python do ambiente onde foi executado `pip install -e .` |
| Timeout ou ligação recusada | Confirmar alimentação, rede, IP, porta e acesso TCP à câmara |
| `DATALEN not found` ou cabeçalho inválido | Confirmar o projeto e o caminho da imagem LIMA no equipamento |
| Erro de descodificação | Confirmar que a resposta contém um BMP completo |
| `Could not open video writer` | Confirmar permissões, espaço livre e suporte ao codec `mp4v` |
| Destino já existente | Escolher outro `--output` ou usar o nome automático |
| Janela indisponível | Executar numa sessão com ambiente gráfico e OpenCV/PyQt5 instalados |

## Limitações reservadas para otimização

A cadência continua a usar `perf_counter()`, um intervalo alvo e `sleep()` quando
há tempo disponível. Cada frame recebido origina um frame gravado; não há
duplicação, interpolação ou compensação temporal. Se a câmara entregar menos FPS
do que o valor fixo do gravador, a duração do vídeo pode diferir do tempo real.

O relógio dos indicadores continua a começar na criação da instância. A revisão
dos indicadores, da precisão temporal, da eficiência de receção e da recuperação
de falhas fica para uma fase posterior. Esta refatoração não garante 20 FPS reais.
