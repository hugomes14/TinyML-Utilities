# Refatoração da organização do repositório — versão 0.2.0

Este documento regista a primeira fase, já concluída. As alterações posteriores
de captura, formato, timestamps e extrator estão descritas no
[guia atual](smartcamera.md) e nas [medições](performance.md).

## Âmbito acordado

- Manter ativas a captura da smartcamera e a interface PyQt5 de extração de frames.
- Arquivar Arduino, firmware, YOLO, anotação e antigos exemplos apenas para consulta.
- Separar código, dados e dependências; documentar em português.
- Preservar a lógica temporal da captura. A otimização e a relação entre FPS e
  duração real do vídeo serão tratadas numa fase posterior.

## Código e configuração

| Origem | Destino |
| --- | --- |
| `src/b6_smart_camera.py` | `src/smartcamera/capture.py` |
| `tests/video_frame_grabber.py` | `src/smartcamera/frame_grabber.py` |
| `src/arduino.py`, `src/yolo.py`, `src/video_utils.py` | `legacy/src/` |
| `src/CameraCaptureRawBytes1/` | `legacy/src/CameraCaptureRawBytes1/` |
| Antigos scripts Python de `tests/` | `legacy/scripts/` |
| `docs/__init__.py` | `legacy/docs/__init__.py` |
| `setup.py` | `legacy/setup.py` |
| `requirements.txt` histórico | `legacy/requirements.txt`, convertido para UTF-8 |
| README local anterior | `legacy/README.previous.md` |

O pacote ativo passa a usar um layout `src/smartcamera/` e metadados em
`pyproject.toml`, com instalação editável. `requirements.txt` remete para essa
instalação, evitando duplicar a lista de dependências. O legado fica fora da
descoberta de pacotes e dos testes automáticos.

A captura ganha parâmetros para IP, porta, FPS e destino, nomes automáticos para
novas gravações, recusa de destinos existentes e fecho de recursos em falhas de
inicialização. O extrator conserva a interface e passa a sugerir as pastas
organizadas e nomes de frames que incluem o vídeo de origem.

Não existe uma camada de compatibilidade nos caminhos antigos. Os antigos
scripts não devem ser usados como pontos de entrada; usa os comandos documentados
no [README](../README.md).

## Integridade da migração

Antes de alterar os módulos ativos, foram verificados os destinos de todos os
movimentos para impedir colisões e saídas da pasta do projeto. Foram movidos
**2 981 ficheiros**, num total de **3 344 145 779 bytes**, em 86 operações.
Os tamanhos e hashes SHA-256 foram comparados antes e depois dos movimentos.

O manifesto dessa verificação está localmente em `data/migration/manifest.json`.
Contém os caminhos de origem e destino, o tamanho e o hash de cada ficheiro no
momento da mudança. Os dois módulos ativos e `legacy/requirements.txt` foram
editados depois dessa verificação; os hashes do manifesto representam o instante
anterior a essas alterações.

Em `data/migration/originals/` ficaram cópias locais dos dois módulos ativos,
do `.gitignore` e do `requirements.txt` anteriores à refatoração. O código legado
e os dados conservaram as alterações locais que já existiam. O ambiente `venv/`
foi mantido no seu local.

## Validação

Os testes em `tests/` cobrem a configuração da captura, receção de mensagens
fragmentadas, descodificação de BMP, recusa de sobreposição de vídeos e fecho de
recursos em caso de falha. A interface é exercitada com um vídeo temporário e
exportação de um frame para um caminho com acentos, em modo Qt `offscreen`.

```powershell
python -m unittest discover -s tests -v
python -m smartcamera.capture --help
python -m smartcamera.frame_grabber --help
```

Estes testes não ligam à smartcamera nem substituem um ensaio real do equipamento.
Após a reorganização, deve confirmar-se a captura na rede da câmara antes de
iniciar os trabalhos de otimização.

Na validação desta refatoração, os **11 testes passaram** em Windows/Python 3.13,
com NumPy 2.4.4, OpenCV 4.13.0.92, Pillow 12.2.0 e PyQt5 5.15.11. A instalação
editável, a ajuda dos dois comandos e `pip check` passaram. A revisão da AST
confirmou que os métodos do protocolo e o ciclo temporal foram preservados,
exceto pela substituição das constantes pelos parâmetros da instância.

Os testes precisaram de ser executados fora do isolamento da ferramenta de
automação devido a erros de permissões de `TemporaryDirectory` no Windows;
não foi necessário alterar o código para esse ambiente.
