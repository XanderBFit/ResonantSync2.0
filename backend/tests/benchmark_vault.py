import timeit

class MockDoc:
    def __init__(self, i):
        self.id = f"id_{i}"
        self._data = {"name": f"track_{i}", "uid": "test-uid", "createdAt": i}

    def to_dict(self):
        return self._data.copy()

def current_implementation(docs):
    results = []
    for d in docs:
        data = d.to_dict()
        data['id'] = d.id
        results.append(data)
    return results

def suggested_optimization(docs):
    return [ {**d.to_dict(), 'id': d.id} for d in docs ]

def list_comp_with_func(docs):
    def transform(d):
        data = d.to_dict()
        data['id'] = d.id
        return data
    return [transform(d) for d in docs]

def benchmark():
    num_docs = 100
    iterations = 10000

    docs = [MockDoc(i) for i in range(num_docs)]

    t1 = timeit.timeit(lambda: current_implementation(docs), number=iterations)
    print(f"Current implementation:   {t1:.4f}s")

    t2 = timeit.timeit(lambda: suggested_optimization(docs), number=iterations)
    print(f"Suggested optimization:   {t2:.4f}s")

    t3 = timeit.timeit(lambda: list_comp_with_func(docs), number=iterations)
    print(f"List comp with func:      {t3:.4f}s")

if __name__ == "__main__":
    benchmark()
