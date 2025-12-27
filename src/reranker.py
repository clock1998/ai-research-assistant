from sentence_transformers import CrossEncoder

model = CrossEncoder('BAAI/bge-reranker-v2-m3', device='cuda')

def rerank_crossencoder(question: str, candidates: list[str]) -> list[float]:
    """
    Given a question and a list of candidate strings, return CrossEncoder relevance scores.
    Args:
        question (str): The input question.
        candidates (list of str): List of candidate answer strings.
    Returns:
        list of float: Scores for each candidate, in order.
    """
    pairs = [(question, candidate) for candidate in candidates]
    scores = model.predict(pairs)
    return scores

# Example usage:
if __name__ == "__main__":
    question = "How many people live in Berlin?"
    candidates = [
        "asd asd asd asd asd asdsa das das dsad sad sad sa dads dasBerlin had a population of 3,520,031 registered inhabitants in an area of 891.82 square kilometers. asdasdasdas das dasdasd asd sad sad asdasd asd asd asd asd asd asd asd asd as dasd as dasd asd asd asd asdas das zxc zxc zxc asd qwewqrwefsdvdsfsd fsdgferg erterg fdsf sdf qwerqweascdasdc dq w erqrfwdcdxzfedqw edasdcasdasdq weqwe asdasdc",
        "Berlin is well known for its museums."
    ]
    scores = rerank_crossencoder(question, candidates)
    print(scores)