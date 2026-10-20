# Medições de captura e leitura

As mudanças foram orientadas por testes de correção e medições locais, seguindo
a skill `python-performance-optimization`. Não se mediu a câmara ou a rede real.

## Método

Foi usado um BMP sintético de 640 × 480, com tons de cinzento de 8 bits e ruído
pseudoaleatório, gerado com seed 42. O socket é simulado em memória e devolve
blocos completos até ao tamanho pedido. Não há latência de rede ou janela.
Os tempos do cliente usam `cProfile` e 100 pedidos após 10 de aquecimento.
São medições indicativas, não um ensaio estatístico de desempenho do equipamento.

| Caso local | Mediana | P95 / observação |
| --- | --- | --- |
| Cliente anterior: cabeçalho byte a byte e descodificação BGR | 0,123 ms | 0,132 ms |
| Cliente novo: buffer em blocos e descodificação nativa | 0,108–0,126 ms | 0,111–0,153 ms, duas execuções |
| Chamadas de receção simuladas por frame | 26 → 2 | Mesmo BMP e cabeçalho |
| Conversão/encode FFV1 e mux, sem profiler | 1,579–1,828 ms | 3,852–3,969 ms, duas execuções |
| Abertura/indexação FFV1 descodificando todas as imagens | 203,0 ms | Mediana de 3 aberturas, 100 frames |
| Abertura/indexação FFV1 pelos pacotes e primeira imagem | 49,9–52,7 ms | Duas execuções, cada uma com 3 aberturas |

Ambiente medido: Windows, Python 3.13.14, PyAV 19.0.1, OpenCV 4.13.0 e
NumPy 2.4.4. A redução de chamadas é verificável; os tempos variam com máquina,
caches, imagem, tamanho, versão e armazenamento. A diferença de centésimos de
milissegundo no cliente não justifica prometer uma melhoria da cadência real.

A captura nova também conserva os tons de cinzento sem os expandir para BGR
na gravação. Para cor, FFV1 usa um formato RGB sem subamostragem de cor, validado
por comparação exata dos arrays descodificados.

O vídeo sintético de 100 frames ocupou cerca de 32,6 MB. O ruído aleatório é pouco
compressível; este valor não serve para estimar o tamanho de um ensaio real.

## Reproduzir o benchmark

```powershell
python scripts/benchmark_capture.py --frames 100
```

O comando produz um diretório único em `data/benchmarks/` com perfil do cliente,
relatório JSON e vídeo/CSV/JSON sintéticos. A gravação usa timestamps artificiais
com intervalos de 50 ms; não espera cinco segundos reais para gerar 100 frames.
O benchmark não liga à câmara, não abre janela e não altera vídeos existentes.
Os relatórios e perfis locais ficam fora do Git.

## Correção verificada

Na versão 0.3.0 passaram **22 testes automáticos**, a instalação editável,
`pip check` e a ajuda dos dois comandos. A interface foi exercitada em Qt
`offscreen`, sem ligação à câmara.

Os testes verificam recuperação exata dos píxeis de tons de cinzento e cor,
timestamps `[0, 100, 370]` ms e duração total de 500 ms com três imagens. O último
frame tem duração explícita de 130 ms; não se inventa uma quarta imagem.
Também cobrem fragmentação TCP, limites, deadline, interrupções, vídeos parciais,
ficheiros existentes, navegação VFR e exportação PNG da imagem visível.

## O que falta medir no equipamento

O CSV de uma sessão real permite distinguir o tempo de resposta da câmara,
descodificação e gravação. O JSON inclui também a pré-visualização. Antes de
introduzir threads, filas ou novos codecs, comparar esses tempos, a cadência
recebida, o consumo de CPU e o espaço de armazenamento durante um ensaio real.

O pipeline continua sequencial e não tem filas que descartem imagens. Um pedido
mais lento reduz a cadência; os timestamps mantêm a duração da sessão. Esta fase
não garante 20 FPS nem precisão de exposição/sincronização do sensor.
