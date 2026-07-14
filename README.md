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
