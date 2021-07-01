


def gripMetricCalc(self, channel, rawChannelData):
    channel = channel[-2:] + 'STD/RMS_Grip'
    minX = min(rawChannelData)
    maxX = max(rawChannelData)
    normalizedData = []
    '''Normalize Data'''
    for i in rawChannelData:
        ix = (i - minX) / (maxX - minX)
        normalizedData.append(ix)
    squaredData = []
    '''Take normalized RMS'''
    for i in normalizedData:
        i = i ** 2
        squaredData.append(i)
    avgSquareData = np.mean(squaredData)
    RMS = math.sqrt(avgSquareData)
    '''Take normalized Std Dev'''
    normalizedDataAvg = np.mean(normalizedData)
    meanSquareData = []
    sumIx = 0
    count = 0
    for i in normalizedData:
        ix = (i - normalizedDataAvg) ** 2
        meanSquareData.append(ix)
        sumIx = ix + sumIx
        count = count + 1
    STDDEV = math.sqrt(sumIx / count)
    value = STDDEV / RMS
