# placar-facil-nuvem
Repositório da aplicação Placar Fácil que utiliza serviços de nuvem.

# Placar Fácil — MVP (AWS: API Gateway + Lambda + S3 + CloudWatch)

**Visão geral:** Placar de partidas rápido, com times configuráveis, sets, pontos por set e vencedor automático (maioria de sets). 

---

## Estrutura do projeto
- `lambda_create_match.py` — cria e salva o JSON de uma partida em S3 (`matches/match-<id>.json`)
- `lambda_get_match.py` — lê e retorna a partida
- `lambda_update_score.py` — atualiza pontuação/sets e calcula vencedor automaticamente
- `static/index.html` — frontend em Bootstrap (coloque o logo em `static/img/logo.png`)
- `README.md` — este arquivo

---

## Formato do JSON por partida
Cada objeto salvo em `s3://<bucket>/matches/match-<id>.json` tem este formato mínimo:

```json
{
  "id": "match-xxxx",
  "name": "Time A x Time B",
  "teamA": "Time A",
  "teamB": "Time B",
  "setsTotal": 3,
  "maxPointsPerSet": 25,
  "sets": [
    {"set":1,"A":25,"B":18,"finished":true},
    {"set":2,"A":18,"B":25,"finished":true}
  ],
  "setsA": 1,
  "setsB": 1,
  "status": "andamento" | "finalizado",
  "vencedor": null | "Time A" | "Time B",
  "createdAt": 1700000000
}
