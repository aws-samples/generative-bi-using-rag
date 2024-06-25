# Generative BI using RAG on AWS
[中文文档](README_CN.md) | [日本語ドキュメント](README_JP.md)

For Deployment Guide, please refer to [CDK Deployment Guide](source/resources/README.md)

This is a comprehensive framework designed to enable Generative BI capabilities on customized data sources (RDS/Redshift) hosted on AWS. It offers the following key features:
- Text-to-SQL functionality for querying customized data sources using natural language.
- User-friendly interface for adding, editing, and managing data sources, tables, and column descriptions.
- Performance enhancement through the integration of historical question-answer ranking and entity recognition.
- Customize business information, including entity information, formulas, SQL samples, and analysis ideas for complex business problems.
- Add agent task splitting function to handle complex attribution analysis problems.
- Intuitive question-answering UI that provides insights into the underlying Text-to-SQL mechanism.
- Simple agent design interface for handling complex queries through a conversational approach.

## Introduction

A NLQ(Natural Language Query) demo using Amazon Bedrock, Amazon OpenSearch with RAG technique.

![Screenshot](./assets/aws-architecture.png)

[User Operation Manual](https://github.com/aws-samples/generative-bi-using-rag/wiki/%E7%94%A8%E6%88%B7%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8C)

[Project Data Flowchart](https://github.com/aws-samples/generative-bi-using-rag/wiki/%E9%A1%B9%E7%9B%AE%E6%B5%81%E7%A8%8B%E5%9B%BE)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

