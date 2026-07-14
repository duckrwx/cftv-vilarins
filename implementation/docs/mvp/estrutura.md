# Estrutura do MVP

Este repositorio esta focado no MVP de cadeia de custodia verificavel para video CFTV usando Bitcoin via OpenTimestamps.

## Pastas principais

- `data/input/`: video original de teste.
- `data/segments/`: segmentos gerados pelo `ffmpeg`.
- `data/packages/`: pacotes SIP BagIt gerados pelo empacotador.
- `data/tampered/`: copias adulteradas para testes controlados.
- `data/ots/`: area auxiliar para provas OpenTimestamps.
- `keys/`: chave privada e chave publica do dispositivo simulado.
- `src/segmenter/`: segmentacao do video.
- `src/packager/`: hashes, manifesto, assinatura e pacote.
- `src/gateway/`: validacao de pacote antes do timestamp.
- `src/anchor/`: geracao de prova OpenTimestamps.
- `src/verifier/`: verificador independente e relatorio pericial.
- `reports/`: relatorios de pacote integro e pacote adulterado.

## Ordem de implementacao

1. `segmenter`
2. `packager`
3. `gateway`
4. `anchor` com OpenTimestamps
5. `verifier`
6. cenarios adulterados
7. paper/site

## Decisao atual

O Raspberry Pi nao e dependencia do primeiro MVP. O container simula o dispositivo de borda. Depois que o fluxo local estiver funcionando, o mesmo codigo pode ser testado em Raspberry para medir viabilidade em hardware real.

Nao ha contrato inteligente nesta versao. Bitcoin entra pela prova OpenTimestamps do manifesto assinado.

