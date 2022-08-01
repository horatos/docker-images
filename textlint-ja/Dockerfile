FROM node:18

USER node

WORKDIR /home/node/textlint

RUN npm init --yes
RUN npm install --save-dev textlint textlint-rule-preset-japanese \
      textlint-plugin-latex2e textlint-rule-preset-ja-technical-writing

ENV FORCE_COLOR=1

WORKDIR /home/node/app

ENTRYPOINT ["/home/node/textlint/node_modules/.bin/textlint"]
