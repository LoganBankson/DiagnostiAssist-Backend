from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

@app.route("/search-articles", methods=["GET"])
def search_articles():
    query = request.args.get("query")
    max_results = request.args.get("limit", 5)

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # Step 1: Search PubMed for PMIDs
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance"
    }
    search_res = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=search_params)
    search_data = search_res.json()
    pmids = search_data.get("esearchresult", {}).get("idlist", [])

    if not pmids:
        return jsonify({"articles": [], "message": "No results found."})

    # Step 2: Get article summaries for those PMIDs
    summary_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }
    summary_res = requests.get(f"{EUTILS_BASE}/esummary.fcgi", params=summary_params)
    summary_data = summary_res.json()

    results = []
    for pmid in pmids:
        item = summary_data.get("result", {}).get(pmid)
        if item:
            results.append({
                "pmid": pmid,
                "title": item.get("title"),
                "authors": item.get("authors", []),
                "journal": item.get("fulljournalname"),
                "pubdate": item.get("pubdate"),
                "source": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })

    return jsonify({"articles": results})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
