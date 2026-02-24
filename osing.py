import json
from opensearchpy import OpenSearch, helpers
from pathlib import Path

OPENSEARCH_URL = "https://search-ai-test-domain-343yonb3wnzzilhdnlbn3cdesm.us-west-1.es.amazonaws.com"
INDEX_NAME = "digital_practice"
USERNAME = "infantsam.antonj@everquint.com"
PASSWORD = "zYWOvQ_pR65Z3cm8'^£{FXw)B?58"

DATA_PATH = Path("/Users/sam/Desktop/sc/sampled/rag_documents.json")

client = OpenSearch(
    hosts=[OPENSEARCH_URL],
    http_auth=(USERNAME, PASSWORD),
    use_ssl=True,
    verify_certs=False
)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    docs = json.load(f)

actions = [
    {
        "_index": INDEX_NAME,
        "_id": doc["doc_id"],
        "_source": doc
    }
    for doc in docs
]

success, failed = helpers.bulk(client, actions)

print("Indexed:", success)
print("Failed:", failed)