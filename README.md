# Persona 5 Royal Compendium and Calculator API 

## Descrição

Este projeto, desenvolvido como parte da pós-graduação em Engenharia de Software na PUC, visa criar um MVP de uma ferramenta para entusiastas de Persona 5 Royal. O projeto consiste em um Compendium e Calculadora de Fusão, proporcionando uma experiência aprimorada para os jogadores que desejam explorar e otimizar suas escolhas de personas.

O Compendium e Calculadora de Fusão para Persona 5 Royal oferece funcionalidades avançadas para os jogadores gerenciarem suas personas de maneira eficiente. O Compendium é uma base de dados completa, apresentando informações detalhadas sobre personas, suas habilidades, resistências e itemizações, dentre outras. Isso permite que os jogadores tomem decisões informadas ao construir suas equipes de personas.

A Calculadora de Fusão é uma ferramenta dinâmica que permite aos usuários experimentar e prever os resultados da fusão entre diferentes personas. Essa funcionalidade facilita a criação de personas mais poderosas, alinhadas com as estratégias individuais dos jogadores. A interface intuitiva da calculadora simplifica o processo de experimentação com diferentes combinações, proporcionando uma abordagem interativa e educacional.


## Conteúdo

- [Dependências](#dependências)
- [Instalação](#instalação)
- [Uso](#uso)

## Dependências


Antes de começar, certifique-se de ter as seguintes ferramentas instaladas em seu ambiente de desenvolvimento:
- Docker: [Instalação do Docker](https://docs.docker.com/desktop/install/linux-install/)
- Python: [Instalação do Python](https://www.python.org/downloads/)
- pip: [Instalação do pip](https://pip.pypa.io/en/stable/installation/)

Opcionalmente também, GNU Make:
- GNU Make: [Instalação do GNU Make](https://www.gnu.org/software/make/#download)


## Instalação

1. Clone o repositório e navegue para a pasta obtida:

```sh
git clone https://github.com/pedro-git-projects/p5r-api.git
cd ./p5r/
```

2. Crie um arquivo .env com as seguintes variáveis de ambiente:

```sh
DATABASE_URL="postgresql://usuario:senha@localhost:27017/db?schema=public"
JWT_SECRET="seu segredo"
POSTGRES_USER=usuario
POSTGRES_PASSWORD=senha
POSTGRES_DB=db
SECRET_KEY="outro segredo"
```

3. Crie um novo ambiente virtual:

```sh
python -m venv venv
```

4. Inicialize o ambiente virtual:

```sh
source ./venv/bin/activate
```

5. Instale as dependências com pip

```sh
pip install -r requirements.txt
```

6. Inicialize o banco de dados:

```
docker-compose up -d
```

```
make init
```

7. Suba a aplicação:

```
make run
```

Caso não tenha o make instalado, basta utilizar os comandos listados nas receitas.

## Uso

A documentação pode ser acessada [http://127.0.0.1:5000/apidocs/#/](http://127.0.0.1:5000/apidocs/#/). 

Essa API faz parte de um trabalho e pode ser facilmente consumida através do frontend disponível [aqui](https://github.com/pedro-git-projects/p5r-calculator-frontend).
