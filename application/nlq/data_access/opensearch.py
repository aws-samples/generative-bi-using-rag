from opensearchpy import OpenSearch
from utils import opensearch

class OpenSearchDao:

    def __init__(self, host, port, opensearch_user, opensearch_password):
        auth = (opensearch_user, opensearch_password)

        # Create the client with SSL/TLS enabled, but hostname verification disabled.
        self.opensearch_client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
    def retrieve_samples(self, index_name, profile_name):
        # search all docs in the index filtered by profile_name
        search_query = {
          "sort": [
            {
              "_score": {
                "order": "desc"
              }
            }
          ],
          "_source": {
              "includes": ["text", "sql"]
          },
          "size": 20,
          "query": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "match_all": {}
                },
                {
                  "match_phrase": {
                    "profile": profile_name
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }

        # Execute the search query
        response = self.opensearch_client.search(
            body=search_query,
            index=index_name
        )

        return response['hits']['hits']

    def add_sample(self, index_name, profile_name, question, answer, embedding):
        record = {
            '_index': index_name,
            'text': question,
            'sql': answer,
            'profile': profile_name,
            'vector_field': embedding
        }

        success, failed = opensearch.put_bulk_in_opensearch([record], self.opensearch_client)
        return success == 1

    def delete_sample(self, index_name, profile_name, doc_id):
        return self.opensearch_client.delete(index=index_name, id=doc_id)

