# Docker Images

いくつかのソフトウェアに追加パッケージをインストールしたDockerイメージです。

## cluttex

[texlive/texlive](https://hub.docker.com/r/texlive/texlive)をベースにして[fswatch](https://github.com/emcrisostomo/fswatch)をインストールしたイメージです。

[cluttex](https://github.com/minoki/cluttex)を利用することを念頭においているため、エントリーポイントを`cluttex`にしています。fswatchがインストールされているので`--watch`オプションを利用することができます。

## textlint-ja

[node](https://hub.docker.com/_/node)をベースにして[textlint](https://github.com/textlint/textlint)といくつかのプリセットをインストールしたイメージです。

インストールされているプリセットやプラグインは以下の通りです。

- textlint-rule-preset-japanese
- textlint-rule-preset-ja-technical-writing
- textlint-plugin-latex2e

## tests

上記のイメージをテストするためのイメージです。以下のコマンドでテストを実行できます。

```
docker compose run --rm tests -m pytest tests
```
