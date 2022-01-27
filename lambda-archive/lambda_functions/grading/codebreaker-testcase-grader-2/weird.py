def Funny(result,problemName,TLE):
    #ANYTHING IN THIS PART AND BELOW IS HARDCODED FOR WEIRD CHECKERS
    if problemName == "1609":
        if result['verdict'] == 'TLE':
            result['score'] = 100
            result['verdict'] = 'AC'
        else:
            delta = min(1,result['runtime']/TLE)
            x = 1.821
            score = (1/x * (x**(delta-1)) -0.25) * 3.344
            result['score'] = min(100,round(Decimal(score)*100,2))
            if result['score'] == 0:
                result['verdict'] = 'WA'
            elif result['score'] == 100:
                result['verdict'] = 'AC'
            else:
                result['verdict'] = 'PS'
                
    #END WEIRD CHECKERS
    
    return result