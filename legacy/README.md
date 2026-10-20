# Código legado — apenas para consulta

Este diretório preserva as ferramentas que deixaram de fazer parte do uso atual.
Não é instalado pelo pacote `smartcamera`, não integra a suite ativa em `tests/`
e não tem garantia de execução.

Os scripts e o firmware foram movidos com as alterações locais existentes.
Os imports, caminhos absolutos, portas COM e referências antigas são históricos;
não foram adaptados à nova organização.

## Inventário

| Caminho | Função histórica |
| --- | --- |
| `src/arduino.py` | `SketchConfig`: compilação/upload por Arduino CLI; `VideoCapture`: captura por série |
| `src/CameraCaptureRawBytes1/CameraCaptureRawBytes1.ino` | Firmware Nano 33 BLE + OV767X, grayscale QVGA, sincronização `0xC0` |
| `src/video_utils.py` | Reprodução, crops positivos/negativos e anotação YOLO |
| `src/yolo.py` | `YOLOHandler`: treino e inferência de deteção de objetos |
| `scripts/test1_yolo_crop.py` | Exemplo interativo de anotação YOLO |
| `scripts/teste1.py` | Reprodução de vídeo |
| `scripts/teste1_1.py` | Recolha de amostras positivas e negativas |
| `scripts/teste2.py` | Exemplo de compilação e upload para Arduino |
| `scripts/teste3.py` | Exemplo de captura por série |
| `scripts/teste4.py` | Exemplo da antiga API `SmartCamera.connection()` |
| `scripts/teste5.py` | Inferência YOLO e exemplo comentado de treino |
| `setup.py` | Configuração histórica do pacote `video-crop` |
| `requirements.txt` | Lista histórica de dependências, convertida de UTF-16 para UTF-8 |
| `README.previous.md` | README local anterior à refatoração; contém caminhos e recomendações desatualizados |
| `src/__init__.py`, `scripts/__init__.py`, `docs/__init__.py` | Marcadores vazios preservados da estrutura antiga |

## Dependências e execução

A lista histórica contém Matplotlib, NumPy, OpenCV, Pillow, pyserial e respetivas
dependências com versões fixas. O código YOLO também exige Ultralytics, que não
estava declarado nessa lista. O Arduino exige Arduino CLI, o core da placa e a
biblioteca `Arduino_OV767X`.

O ficheiro `requirements.txt` é uma referência histórica, não uma receita de
instalação validada para o Python atual. Não o instales no ambiente ativo apenas
para usar a smartcamera.

Vários scripts executam ações ao serem importados, incluindo abertura de janelas,
ligação a portas série ou upload de firmware. A preservação para consulta não
implica que devam ser executados como testes automáticos.

`scripts/teste4.py` já referia uma classe substituída antes desta organização.
A API ativa é agora `smartcamera.capture.SmartCameraStableFPS`; não existe uma
camada de compatibilidade para os antigos imports `src.*`.

## Dados associados

Os vídeos, datasets, pesos e resultados continuam locais em [`../data/`](../data/README.md).
Consulta o [mapa de migração](../docs/data-layout.md) antes de recuperar um exemplo.
Para voltar a usar alguma ferramenta, recupera-a como uma alteração própria,
revendo dependências e caminhos.
