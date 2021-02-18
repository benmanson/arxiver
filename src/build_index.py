import os
import json
import re
import preprocessing
import time
import numpy as np
import utils
from config import *
from tqdm import tqdm

def get_paper_from_json(json_string):
    p = json.loads(json_string)                 # load the paper as a json object
    
    paper = dict()

    paperID = p["id"]

    # remove newlines and ignore unicode characters
    total_content = p["abstract"].replace('\n', ' ').encode('ascii', 'ignore') + b' ' + p["content"].replace('\n', ' ').encode('ascii', 'ignore')

    # get other metadata
    paper["title"] = p["title"]                 # title
    paper["authors"] = p["authors"]             # authors
    d = ""
    for v in p["versions"]:
        if v["version"] == "v1":
            d = v["created"]
            break
    paper["date"] = d                           # date submitted (e.g. [Day], [d] [Mon] [y] HH:MM:ss [Zone])
    paper["categories"] = p["categories"]       # categories
    paper["content"] = str(total_content)       # content of paper

    return paper, paperID

def build_papers_index(filename):
    with open(filename, "rb") as f:
        papers_as_json = f.readlines()          # since one paper in json per line

        paper_index = dict()

        for p in papers_as_json:
            paper, paperID = get_paper_from_json(p)
            paper_index[paperID] = paper
    
    return paper_index

def build_inverted_index(papers_index, debug=False):
    """
        Build index of the form:
            { term: { doc_frequency,
                      doc_positions: 
                            { docID: [pos1, pos2, ...],
                              docID: [pos1, pos2, ...]}
                    }
            }
    """
    # start_time = time.time()

    # get the unique terms in the paper index
    unique_terms = set()
    for paperID in tqdm(list(papers_index.keys()), ascii=True, desc="Getting unique terms from papers."):
        content = papers_index[paperID]["content"]
        content = preprocessing.tokenise(content)
        unique_terms |= set(content)
    
    index = dict()
    
    # construct the index and initialize the dictionary at each term
    for term in sorted(unique_terms):
        term_info = {"doc_frequency": 0,
                     "doc_positions": dict()
                    }
        index[term] = term_info
    
    # loop through the papers and update the index
    for paperID in tqdm(list(papers_index.keys()), ascii=True, desc="Building index"):
        content = papers_index[paperID]["content"]
        content = preprocessing.tokenise(content)

        terms = set(content)
        for t in terms:
            index[t]["doc_frequency"] += 1

        for i, word in enumerate(content):
            try:
                index[word]["doc_positions"][paperID].append(i)
            except:
                index[word]["doc_positions"][paperID] = []
                index[word]["doc_positions"][paperID].append(i)

    # pop all the stop words from the index
    if STOPPING:
        for sw in STOP_WORDS:
            try:
                index.pop(sw)
            except KeyError:
                pass
    else:
        try:
            index.pop("")
        except KeyError:
            pass
    # end_time = time.time()

    # if debug flag set, print some information about the data
    if debug:
        # print(STOP_WORDS)
        print(len(list(index.keys())))
        print(index["test"])
        try:
            print(index[""])
        except:
            pass
        # print("Took {} seconds to build.".format(round(end_time - start_time, 2)))

    return index

def main():
    papers_index = build_papers_index(JSON_PATH)
    # print(len(list(papers_index.keys())))
    inverted_index = build_inverted_index(papers_index, debug=True)
    utils.save_index(inverted_index)

if __name__=="__main__":
    main()