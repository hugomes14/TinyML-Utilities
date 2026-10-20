# Smartcamera: captura, tempos e extração

## Âmbito e formato

A captura atual usa **Matroska + FFV1**, sem perdas, com cadência variável (VFR).
Conserva cada resposta válida uma vez, à resolução nativa, sem redimensionar nem
adicionar indicadores aos píxeis gravados. Os indicadores existem apenas na janela.
O extrator exporta o frame visível e usa timestamps do vídeo.

O suporte atual é para BMP com píxeis de 8 bits em tons de cinzento, BGR ou BGRA.
Uma mudança de resolução ou canais durante a sessão provoca uma paragem com erro.
Os ficheiros são maiores do que MP4 com compressão com perdas; o tamanho depende
do conteúdo. Os MP4/AVI históricos não são convertidos nem alterados.

## Comandos

Instala com `python -m pip install -e .` e usa o Python desse ambiente:

```powershell
python -m smartcamera.capture --ip 192.168.249.197 --port 33040 --fps 20
python -m smartcamera.capture --output data/videos/captures/ensaio_01.mkv
python -m smartcamera.capture --timeout 5 --no-save
```

| Opção | Predefinição | Efeito |
| --- | --- | --- |
| `--ip` | `192.168.249.197` | IP ou hostname da câmara |
| `--port` | `33040` | Porta TCP, entre 1 e 65535 |
| `--fps` | `20` | Ritmo alvo dos pedidos; não impõe FPS fixos à gravação |
| `--timeout` | `5` | Prazo total de envio/receção de uma resposta, em segundos |
| `--output` | Nome gerado em `data/videos/captures/` | Novo `.mkv`, com CSV e JSON acompanhantes |
| `--no-save` | Desativado | Apenas visualização; incompatível com `--output` |
| `--help` | — | Ajuda sem ligação ou janelas |

Os nomes automáticos incluem data, hora e microssegundos locais do computador.
As pastas de destino são criadas. Nenhum dos três destinos pode já existir.
`q` termina normalmente; `Ctrl+C` termina como interrupção. O modo de utilização
continua manual, com janela; não há paragem programada ou reconexão automática.

## Origem e representação do tempo

- Usa-se `perf_counter_ns()` para intervalos monotónicos, independente de ajustes
  ao relógio civil. A unidade em nanossegundos não garante exatidão dessa ordem.
- Registam-se início do pedido e receção completa da resposta no computador.
- A origem temporal é o instante de receção do primeiro BMP completo, antes da
  descodificação. A ligação e a preparação da janela ficam fora desse intervalo.
- O instante UTC do computador também é guardado por frame para referência civil.
- O timestamp do vídeo é o tempo desde essa origem, arredondado ao milissegundo.
  O CSV conserva o intervalo original em nanossegundos. Se dois timestamps não
  forem distintos nessa resolução, a sessão termina com erro em vez de inventar tempos.
- A duração de apresentação de um frame vai até à chegada do seguinte. A do último
  vai até à paragem. Não se acrescentam imagens para preencher intervalos.

Estes tempos não medem a exposição no sensor. A resposta pode incluir atrasos
do projeto da câmara, transporte e sistema operativo. Pedidos distintos também
não garantem exposições distintas se a própria câmara devolver uma imagem em cache.
Para sincronização com outros equipamentos, é necessário suporte adicional da câmara.

## Metadados

Cada `.mkv` acompanha os seguintes ficheiros com o mesmo nome base.

### CSV por frame: `.frames.csv`

| Campo | Significado |
| --- | --- |
| `frame_index` | Índice guardado, a começar em 1 |
| `request_started_ns` | Relógio monotónico no início do pedido |
| `received_ns` | Relógio monotónico após a receção completa |
| `received_utc` | Hora UTC do computador junto da receção |
| `elapsed_ns` | Intervalo desde a primeira receção completa |
| `video_pts_ms` | Timestamp de apresentação escrito no vídeo |
| `response_bytes` | Número de bytes BMP recebidos |
| `request_receive_ms` | Tempo entre início do pedido e receção completa |
| `decode_ms` | Tempo entre receção e conclusão da descodificação, incluindo anotação UTC |
| `record_ms` | Conversão/encode do frame e mux do pacote anterior |

O CSV é descarregado para o sistema operativo após cada linha. `record_ms` não
inclui a escrita da própria linha CSV, nem a finalização do contentor.

### Resumo: `.session.json`

Contém versão do esquema, configuração, origem temporal, dimensões/canais,
codec, número de frames, duração e motivo da paragem. O estado inicial é
`recording`; os estados finais são `completed`, `interrupted` e `error`.
O resumo inclui contagens, médias e máximos de receção, descodificação,
gravação e pré-visualização. Os tempos por frame permitem outras análises offline.

Se a ligação falhar antes do primeiro frame, o JSON contém o erro, o CSV só tem
cabeçalho e o `.mkv` pode estar vazio. Não se trata de um vídeo utilizável.
Uma terminação abrupta do processo pode deixar estado `recording` e um vídeo
incompleto; o fecho controlado não é uma garantia contra corte de energia.

## Protocolo e tratamento de falhas

O cliente TCP envia o pedido ASCII:

```xml
<LIMA DIR="Request" CMD="Project_GetImage" TYPE="BMP" PATH="Module Application.Smart Camera.Image Monochrome.Grey"/>
```

Lê até ao terminador `>` e extrai `DATALEN`. O cabeçalho está limitado a 2048
bytes e a imagem a 64 MiB. Leituras em blocos conservam os bytes do BMP que
chegarem juntamente com o cabeçalho. Depois recebem-se exatamente os bytes em falta.
O prazo de resposta é total por pedido, mesmo que cheguem pequenos blocos.

Timeout, desconexão, resposta inválida, falha de descodificação ou gravação
terminam a sessão. O cliente e a janela são fechados e tenta-se finalizar o
vídeo e os metadados já produzidos. Não se volta a ligar silenciosamente.
Se houver uma falha de disco, não é possível garantir a finalização dos ficheiros.

O último frame pode permanecer visível no vídeo durante a espera que terminou
em timeout. O JSON marca a sessão como `error`, e o CSV identifica quando ocorreu
a última receção; esse intervalo não representa novas imagens da câmara.

## Organização do código

| Módulo | Responsabilidade |
| --- | --- |
| `client.py` | TCP/LIMA, limites, deadline, descodificação nativa e tempos de receção |
| `recording.py` | FFV1/VFR, duração de pacotes, CSV, JSON e estatísticas |
| `capture.py` | Opções, ritmo dos pedidos, janela e ciclo de vida da sessão |
| `video.py` | Índice de frames, timestamps reais e leitura do frame selecionado |
| `frame_grabber.py` | Interface PyQt5 e exportação da imagem visível |

```python
from smartcamera.capture import SmartCameraCapture

camera = SmartCameraCapture(
    ip="192.168.249.197", port=33040, fps=20,
    output_path="data/videos/captures/ensaio_02.mkv", timeout=5,
)
camera.run()
```

O nome `SmartCameraStableFPS` continua como alias por compatibilidade de import;
não implica garantia de FPS estáveis. O destino agora tem de ser `.mkv`.

## Extrator e desempenho

```powershell
python -m smartcamera.frame_grabber --videos-dir data/videos --frames-dir data/frames
```

O leitor indexa timestamps ao abrir. Nas capturas FFV1, usa os pacotes sem
descodificar todas as imagens. Para outros codecs, percorre a descodificação
para obter uma contagem e timestamps corretos; vídeos longos podem demorar a abrir.
Só conserva a imagem atualmente selecionada, além do índice temporal.

Uma abertura falhada conserva o vídeo anterior. Uma leitura falhada conserva o
frame visível e repõe o slider. Redimensionamento e exportação usam a imagem em
memória, sem novo seek/decode. PNG preserva píxeis; JPEG continua disponível com perdas.

Consulta as [medições e limitações](performance.md). Não se pode inferir a
cadência real da câmara a partir do benchmark sintético.

## Referências técnicas

- [Tempos e PTS no PyAV](https://pyav.org/docs/stable/api/time.html)
- [Codificação de arrays NumPy com PyAV](https://pyav.org/docs/stable/cookbook/numpy.html)
- [FFV1 no FFmpeg](https://ffmpeg.org/ffmpeg-codecs.html#ffv1)
