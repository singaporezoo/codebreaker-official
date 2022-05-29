# https://www.questionpro.com/blog/pearson-correlation-coefficient/
def pearsonr(X,Y):
    assert(sum(X) != 0)
    assert(sum(Y) != 0)
    N = len(X)
    A = N*sum([X[i]*Y[i] for i in range(N)])
    B = sum(X) * sum(Y)
    C = N * sum([i**2 for i in X]) - sum(X)**2
    D = N * sum([i**2 for i in Y]) - sum(Y)**2
    E = (A - B)/(C *D)**0.5

    return E