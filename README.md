# CKAN em Docker | Projeto Presenças | TCC 2024/2025

Este repositório contém um tarball com o CKAN do Projeto Presenças. Esta instância de CKAN já possui três artistas cadastrados para exemplo. Exceto pela extensão escrita para o projeto ([encontrada aqui](https://github.com/thiagoc01/ckanext-presencas)), as demais são originais da desenvolvedora do CKAN, e as de terceiros documentadas.

Ele é baseado [no repositório original](https://github.com/ckan/ckan-docker/). Exceto pelo NGINX, os demais serviços são utilizados. A estrutura abaixo é para Docker Standalone. Para Docker Swarm, adapte para a estrutura do mesmo. Para dicas, consulte o [repositório da aplicação auxiliar que conecta ao CKAN](https://github.com/thiagoc01/presencas-tcc).

## Dependências

- Docker
- Docker Compose V2

## Como executar?

Extraia o tarball em diretório. Dentro do diretório, siga os passos abaixo.

1 - Executar
```bash
$ sudo docker network create ckan-marilu
```
2 - Executar os comandos abaixo para construir a imagem do CKAN 2.11.0
```bash
$ cd ckan && sudo docker build -t ckan:2.11.0 . && cd ..
```

3 - Executar os comandos abaixo para construir a imagem do datapusher
```bash
$ cd datapusher-plus-docker/datapusher-plus/0.15.0 && sudo docker build -t datapusher-plus-final . && cd ../../..
```

4 - Executar
```bash
$ sudo chown -R 70:70 persistencia/banco_dados && sudo chown -R 502:502 persistencia/bibliotecas-python/ && sudo chown -R 503:502 persistencia/dados/ && sudo chown -R 8983:8983 persistencia/solr/
```

5 - No arquivo .env, altere as variáveis CKAN_SITE_URL e CKAN__DATAPUSHER__CALLBACK_URL_BASE para o IP da sua interface de rede.

6 - Execute
```bash
$ sudo docker compose up -d
```

A aplicação estará disponível na porta 5000 se tudo estiver correto. A conta de administrador cadastrada é da gerente do Projeto Presenças. A credencial pode ser encontrada no arquivo .env.

**É importante lembrar que os recursos não aparecerão, já que as URLs terão o IP de origem incorreto.
Para corrigir, basta utilizar [este código](https://gist.github.com/thiagoc01/28e03461aa0f88d6593d005ed61ced04).
Altere os campos entre <> para os valores corretos. Você deve executar este código dentro do container do CKAN ou qualquer um com Python 3 dentro da rede dos containers.**

:warning: Lembre-se! Não utilize este CKAN em produção. Caso deseje, altere todos os segredos, chaves e senhas.