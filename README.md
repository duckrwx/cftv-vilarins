# CFTV Verificavel

Artigo web do projeto de Topicos em Engenharia, UnB 2026.1.

Este repositorio contem:

- artigo web publicado via GitHub Pages na raiz do repositorio;
- codigo-fonte do MVP em `implementation/`;
- slides e prints de prova usados na apresentacao.

Pagina publicada via GitHub Pages em:

```text
https://cftv.vilarins.cloud
```

Secao do problema:

```text
https://cftv.vilarins.cloud/#problema
```

Slides para gravacao do video:

```text
https://cftv.vilarins.cloud/slides.html
```

Prints de prova:

```text
https://cftv.vilarins.cloud/provas.html
```

Video de apresentacao:

```text
https://youtu.be/PR9o8jA2Crk
```

Repositorio da disciplina:

```text
https://github.com/Prof-Edil/projeto-final-vilarins
```

## Codigo-fonte

O codigo-fonte da implementacao esta em:

```text
implementation/
```

Principais componentes:

- `implementation/src/segmenter/`: segmentacao do video.
- `implementation/src/packager/`: hashes, manifesto, assinatura e pacote.
- `implementation/src/gateway/`: validacao do pacote antes do timestamp.
- `implementation/src/anchor/`: carimbo OpenTimestamps.
- `implementation/src/verifier/`: verificacao independente.
- `implementation/docs/mvp/`: documentacao de execucao e estrutura.

## OpenTimestamps

A integracao com OpenTimestamps esta implementada em:

- `implementation/src/anchor/stamp_manifest.py`: gera a prova `.ots` do manifesto assinado.
- `implementation/src/verifier/verify_package.py`: verifica o pacote e a prova OpenTimestamps.
- `implementation/docs/mvp/execucao-local.md`: documenta o fluxo de stamp, upgrade e verificacao.
- `implementation/requirements.txt`: inclui `opentimestamps-client`.

As provas visuais da confirmacao em Bitcoin estao em:

```text
https://cftv.vilarins.cloud/provas.html
```

Para executar localmente:

```text
cd implementation
bash scripts/generate_sample_video.sh
python3 src/segmenter/segment_video.py
python3 src/packager/create_package.py
python3 src/gateway/validate_package.py
python3 src/anchor/stamp_manifest.py
python3 src/verifier/verify_package.py
```
