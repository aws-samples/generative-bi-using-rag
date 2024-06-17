# AWS上でRAGを使用した生成型BI

このフレームワークは、AWS上でカスタマイズされたデータソース（RDS/Redshift）に対して生成型BI機能を有効にするためのものです。以下の主要な機能を提供します：
- 自然言語を使用してカスタマイズされたデータソースをクエリするためのText-to-SQL機能。
- データソース、テーブル、および列の説明を追加、編集、および管理するためのユーザーフレンドリーなインターフェース。
- 歴史的な質問-回答のランキングとエンティティ認識を統合することによるパフォーマンスの向上。
- エンティティ情報、公式、SQLサンプル、複雑なビジネス問題の分析アイデアなど、ビジネス情報のカスタマイズ。
- 複雑な帰属分析問題を処理するためのエージェントタスク分割機能の追加。
- 基盤となるText-to-SQLメカニズムについての洞察を提供する直感的な質問応答UI。
- 対話的なアプローチを通じて複雑なクエリを処理するためのシンプルなエージェント設計インターフェース。

## 導入

Amazon BedrockとAmazon OpenSearchを使用したNLQ（自然言語クエリ）デモです。

![スクリーンショット](./assets/screenshot-genbi.png)

[ユーザー操作マニュアル](https://github.com/aws-samples/generative-bi-using-rag/wiki/%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8C)

[プロジェクトデータフローチャート](https://github.com/aws-samples/generative-bi-using-rag/wiki/%E9%A1%B9%E7%9B%AE%E6%B5%81%E7%A8%8B%E5%9B%BE)

## デプロイガイド

### 1. EC2インスタンスの準備
以下の設定でEC2を作成します：

    - OSイメージ（AMI）：Amazon Linux 2023、Amazon Linux 2（AL2のサポート終了は2025-06-30）
    - インスタンスタイプ：t3.largeまたはそれ以上
    - VPC：デフォルトを使用し、パブリックサブネットを選択
    - セキュリティグループ：22、80、8000ポートへのアクセスをどこからでも許可（「SSHトラフィックをどこからでも許可」と「インターネットからのHTTPトラフィックを許可」を選択）
    - ストレージ（ボリューム）：1 GP3ボリューム - 30 GiB

### 2. 権限の設定

2.1 IAMロールの権限

新しいIAMロールを作成し、名前をgenbirag-service-roleとします。設定は以下の通りです：
   - 信頼されたエンティティタイプ：AWSサービス
   - サービス：EC2
   - 使用事例：EC2 - EC2インスタンスが代わりにAWSサービスを呼び出すことを許可します。

「権限の追加」をスキップして、まずこのロールを作成します。

ロールが作成されたら、インラインポリシーを作成して以下の権限を追加します：
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "bedrock:*",
                "dynamodb:*"
            ],
            "Resource": "*"
        }
    ]
}
```

最後に、このIAMインスタンスプロファイル（IAMロール）をEC2インスタンスにバインドします。

2.2 Amazon Bedrockのモデル権限

Anthropic ClaudeモデルとAmazon Titan埋め込みモデルのモデルアクセスを、AWSコンソールのus-west-2（オレゴン）リージョンで有効にしていることを確認してください。
![Bedrock](assets/bedrock_model_access.png)

### 3. DockerとDocker Composeのインストール

EC2インスタンスにSSHコマンドでec2-userユーザーとしてログインするか、EC2コンソールのEC2インスタンスコネクト機能を使用してコマンドラインにログインします。

セッションで、以下のコマンドを実行します。**注：各コマンドを1行ずつ実行してください。**

このユーザーでない場合は、以下のコマンドで切り替えることができます：
```bash
sudo su - ec2-user
```

```bash  
# コンポーネントのインストール
sudo yum install docker python3-pip git -y && pip3 install -U awscli

# Amazon Linux 2の場合、dnfをyumで置き換えることができます

sudo yum install docker python3-pip git -y && pip3 install -U awscli && sudo pip3 install docker-compose

# docker pythonラッパー7.0 SSLバージョンの問題を修正  
pip3 install docker==6.1.3

# コンポーネントの設定
sudo systemctl enable docker && sudo systemctl start docker && sudo usermod -aG docker $USER

# ターミナルを終了
exit
```

### 4. デモアプリケーションのインストール

ターミナルセッションを再開し、以下のコマンドを続けて実行します：

注：各コマンドを1行ずつ実行してください。

```bash
# ユーザーec2-userとしてログイン

# OpenSearchサーバーパラメータの設定
sudo sh -c "echo 'vm.max_map_count=262144' > /etc/sysctl.conf" && sudo sysctl -p

# コードのクローン
git clone https://github.com/aws-samples/generative-bi-using-rag.git

# .envファイルで環境変数を設定し、AWS_DEFAULT_REGIONをEC2インスタンスと同じリージョンに変更
cd generative-bi-using-rag/application && cp .env.template .env 

# ローカルでdockerイメージをビルド
docker-compose build

# すべてのサービスを起動
docker-compose up -d

# MySQLとOpenSearchの初期化が完了するまで3分待機
sleep 180
```

### 5. MySQLの初期化

ターミナルで以下のコマンドを続けて実行します：
```bash
cd initial_data && wget https://github.com/fengxu1211/generative-bi-using-rag/raw/demo_data/application/initial_data/init_mysql_db.sql.zip

unzip init_mysql_db.sql.zip && cd ..

docker exec nlq-mysql sh -c "mysql -u root -ppassword -D llm  < /opt/data/init_mysql_db.sql"
```

### 6. Amazon OpenSearch dockerバージョンの初期化

6.1 新しいインデックスを作成してサンプルデータのインデックスを初期化
```bash
docker exec nlq-webserver python opensearch_deploy.py
```

スクリプトの実行が何らかのエラーで失敗した場合は、以下のコマンドでインデックスを削除し、前のコマンドを再実行してください。
```bash
curl -XDELETE -k -u admin:admin "https://localhost:9200/uba"
```

6.2 (オプション)既存のインデックスにデータを追加してカスタムQAデータを一括インポート
```bash
docker exec nlq-webserver python opensearch_deploy.py custom false
```

### 7. Streamlit Web UIへのアクセス

ブラウザでURLを開きます：`http://<your-ec2-public-ip>` 

注：HTTPを使用し、HTTPSではありません。

### 8. APIへのアクセス

ブラウザでURLを開きます：`http://<your-ec2-public-ip>:8000` 

注：HTTPを使用し、HTTPSではありません。

デフォルトのアカウントは

```
username: admin
password: # 以下の手順に従ってパスワードを設定してください
```

パスワードを変更するか、ユーザー名を追加する場合は、以下のファイルを変更できます。

application/config_files/stauth_config.yaml

例えば

```yaml
credentials:
  usernames:
    jsmith:
      email: jsmith@gmail.com
      name: John Smith
      password: abc # ハッシュ化されたパスワードに置き換える
    rbriggs:
      email: rbriggs@gmail.com
      name: Rebecca Briggs
      password: def # ハッシュ化されたパスワードに置き換える
cookie:
  expiry_days: 30
  key: random_signature_key # 文字列である必要があります
  name: random_cookie_name
preauthorized:
  emails:
  - melsby@gmail.com
```

パスワードを平文からハッシュ化されたパスワードに変更するには、以下の方法で取得できます。

```python
from streamlit_authenticator.utilities.hasher import Hasher
hashed_passwords = Hasher(['abc', 'def']).generate()
```


## デモアプリケーションでカスタムデータソースを使用する方法
1. 最初に、Data Connection ManagementおよびData Profile Managementページで対応するData Profileを作成します。

![AddConnect](assets/add_database_connect.png)

2. Data Profileを選択した後、質問を開始します。簡単な質問に対しては、LLMが直接正しいSQLを生成できます。生成されたSQLが正しくない場合は、Schemaに注釈を追加してみてください。

![CreateProfile](assets/create_data_profile.png)

このWebページを更新し、Fetch table definitionをクリックします。

![UpdateProfile](assets/update_data_profile.png)

3. Schema Managementページを使用し、Data Profileを選択した後、テーブルとフィールドにコメントを追加します。これらのコメントは、LLMに送信されるプロンプトに含まれます。
   (1) いくつかのフィールドのAnnotation属性に、そのフィールドに表示される可能性のある値を追加します。例："Values: Y|N", "Values: 上海市|江蘇省"
   (2) テーブルのコメントに、ビジネスの質問に答えるためのドメイン知識を追加します。

![AddSchema](assets/add_schema_management.png)


![UpdateSchema](assets/update_schema_management.png)

4. 再度質問をします。正しいSQLを生成できない場合は、Sample QAペアをOpenSearchに追加します。
   (1) Index Managementページを使用し、Data Profileを選択した後、QAペアを追加、表示、削除できます。

![AddIndex](assets/add_index_sample.png) 

5. 再度質問をします。理論的には、RAGアプローチ（PEはFew shotsを使用）が正しいSQLを生成できるはずです。

## セキュリティ

詳細については、[CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications)を参照してください。

## ライセンス

このライブラリはMIT-0ライセンスの下でライセンスされています。LICENSEファイルを参照してください。
