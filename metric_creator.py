import os
import csv
import sys
import ast
import pandas as pd
import numpy as np
import math
from sklearn import preprocessing
import tkinter as tk
from tkinter import filedialog

class metricCreator:

    def __init__(self):
        self.trackName = 'WorkflowAttributes.csv'
        self.mappingFile = 'OutputChannelDef.csv'
        self.resultsFile = 'SPFResults_0.csv'

    def loopResults(self, simFilePathDirectory, file_list, trackName):
        metricResults = []
        gripList = []
        for run in file_list:
            print(run)
            segments = metricCreator.segments(simFilePathDirectory, run, trackName)
            dataDict, headers, conversionDict = metricCreator.segmentData(simFilePathDirectory, run, segments)
            dataDict = metricCreator.englishUnitConvert(dataDict, conversionDict)
            runResults = metricCreator.metricCalcs(simFilePathDirectory, run, dataDict, headers)
            gripListT34 = {'T34LFSTD/RMS_Grip': runResults['T34LFSTD/RMS_Grip'],
                           'T34RFSTD/RMS_Grip': runResults['T34RFSTD/RMS_Grip'],
                           'T34LRSTD/RMS_Grip': runResults['T34LRSTD/RMS_Grip'],
                           'T34RRSTD/RMS_Grip': runResults['T34RRSTD/RMS_Grip']}
            gripList.append(gripListT34)
            metricResults.append(runResults)
        return gripList, metricResults

    def segments(self, simFilePathDirectory, run, trackName):
        try:
            runData = {}
            '''Get Split Data if VES run'''
            if not batch:
                with open(simFilePathDirectory + '/' + run + '/' + self.trackName, newline='') as workflowAttributes:
                    reader = csv.reader(workflowAttributes, delimiter=',', quotechar='"')
                    for row in reader:
                        if row[0] == 'Event_Site':
                            trackName = row[1]

            with open('C:/ProgramData/PrattMiller/Track_Paths/TrackSplits.csv', newline='') as trackSplitCSVFile:
                reader = csv.reader(trackSplitCSVFile, delimiter=',')
                headers = []
                trackSegments = {}
                for row in reader:
                    if row[0] == 'Headers':
                        for i in range(1, len(row)):
                            headers.append(row[i])
                    if row[0] == trackName:
                        outTime = float(row[1])
                        for i in range(2, len(row)):
                            if row[i] != 0:
                                trackSegments[headers[i-1]] = round(float(row[i]) + outTime, 2)
        except Exception as error:
            print(error)
            print('Error Getting Segments')
            sys.exit()

        '''This needs to be written as a function for Pocono or RC events.  For now hardcoded for 2 turns entry, mid,
        exit'''
        segments = {
            'T1Entry': [trackSegments['T1Entry'], trackSegments['T1Mid']],
            'T12Mid': [trackSegments['T1Mid'], trackSegments['T2Mid']],
            'T2Exit': [trackSegments['T2Mid'], trackSegments['T2Exit']],
            'T12': [trackSegments['T1Entry'], trackSegments['T2Exit']],
            'T3Entry': [trackSegments['T3Entry'], trackSegments['T3Mid']],
            'T34Mid': [trackSegments['T3Mid'], trackSegments['T4Mid']],
            'T4Exit': [trackSegments['T4Mid'], trackSegments['T4Exit']],
            'T34': [trackSegments['T3Entry'], trackSegments['T4Exit']]
        }
        return segments

    def segmentData(self, simFilePathDirectory, run, segments):
        with open(simFilePathDirectory + '/' + run + '/' + self.resultsFile, newline='') as resultData:
            reader = csv.reader(resultData, delimiter=',', quotechar='"')
            resultDataList = []
            resultDataDict = {}
            i = 0
            for row in reader:
                if i == 0:
                    headers = row
                    i = 1
                else:
                    resultDataList.append(row)
            with open(simFilePathDirectory + '/' + run + '/' + self.mappingFile, newline='') as mappingData:
                reader = csv.reader(mappingData, delimiter=',', quotechar='"')
                headersDict = {}
                conversionDict = {}
                for row in reader:
                    headersDict[row[1]] = row[2]
                    conversionDict[row[2]] = {}
                    conversionDict[row[2]]['unit'] = row[3]
                    conversionDict[row[2]]['convfactor'] = row[6]
                headersDict['vehicle.wheel_1.summary_fW_z'] = 'Wheel_Load_LF'
                headersDict['vehicle.wheel_2.summary_fW_z'] = 'Wheel_Load_RF'
            headersUpdated = []
            for header in headers:
                if header in headersDict:
                    headersUpdated.append(headersDict[header])
                else:
                    headersUpdated.append(header)
            for key in segments:
                resultDataDict[key] = {}
                for header in headersUpdated:
                    resultDataDict[key][header] = []
                start = segments[key][0]
                end = segments[key][1]
                for row in resultDataList:
                    if start <= float(row[0]) <= end:
                        for i in range(1, len(row)):
                            resultDataDict[key][headersUpdated[i]].append(float(row[i]))

            for key in resultDataDict:
                resultDataDict[key].pop('Time')

            return resultDataDict, headersUpdated, conversionDict

    def englishUnitConvert(self, dataDict, conversionDict):
        for key in dataDict:   ## segments
            for channel in dataDict[key]:  ## channel list in segment
                data = dataDict[key][channel]
                newData = []
                for i in data:
                    newData.append(float(i) * float(conversionDict[channel]['convfactor']))
                dataDict[key][channel] = newData

        return dataDict

    def metricCalcs(self, simFilePathDirectory, run, dataDict, headers):
        runMetricResults = {}
        for key in dataDict:
            for channel in dataDict[key]:
                rawChannelData = dataDict[key][channel]
                try:
                    if channel in ['Wheel_Load_LF', 'Wheel_Load_RF', 'Wheel_Load_LR', 'Wheel_Load_RR']:
                        resultsDict = self.gripMetricCalc(channel, rawChannelData)
                        runMetricResults[key + resultsDict['channel']] = resultsDict['value']
                    else:
                        runMetricResults[key + channel + 'min'] = min(rawChannelData)
                        runMetricResults[key + channel + 'max'] = max(rawChannelData)
                        runMetricResults[key + channel + 'avg'] = np.mean(rawChannelData)
                except:
                    print('No Data for ' + key + ' ' + channel)

        return runMetricResults

    # def gripMetricCalc(self, channel, rawChannelData):
    #     channel = channel[-2:] + 'STD/RMS_Grip'
    #     minX = min(rawChannelData)
    #     maxX = max(rawChannelData)
    #     normalizedData = []
    #     '''Normalize Data'''
    #     for i in rawChannelData:
    #         ix = (i - minX) / (maxX - minX)
    #         normalizedData.append(ix)
    #     squaredData = []
    #     '''Take normalized RMS'''
    #     for i in normalizedData:
    #         i = i ** 2
    #         squaredData.append(i)
    #     avgSquareData = np.mean(squaredData)
    #     RMS = math.sqrt(avgSquareData)
    #     '''Take normalized Std Dev'''
    #     normalizedDataAvg = np.mean(normalizedData)
    #     meanSquareData = []
    #     sumIx = 0
    #     count = 0
    #     for i in normalizedData:
    #         ix = (i - normalizedDataAvg)**2
    #         meanSquareData.append(ix)
    #         sumIx = ix + sumIx
    #         count = count + 1
    #     STDDEV = math.sqrt(sumIx / count)
    #     value = STDDEV / RMS
    #
    #     d = {'channel': channel, 'value': value}
    #
    #     return

    def gripMetricCalc(self, channel, rawChannelData):
        channel = channel[-2:] + 'STD/RMS_Grip'
        minX = min(rawChannelData)
        maxX = max(rawChannelData)
        # normalizedData = []
        # '''Normalize Data'''
        # for i in rawChannelData:
        #     ix = (i - minX) / (maxX - minX)
        #     normalizedData.append(ix)
        squaredData = []
        '''Take normalized RMS'''
        for i in rawChannelData:
            i = i ** 2
            squaredData.append(i)
        avgSquareData = np.mean(squaredData)
        RMS = math.sqrt(avgSquareData)
        '''Take normalized Std Dev'''
        rawChannelDataAvg = np.mean(rawChannelData)
        meanSquareData = []
        sumIx = 0
        count = 0
        for i in rawChannelData:
            ix = (i - rawChannelDataAvg) ** 2
            meanSquareData.append(ix)
            sumIx = ix + sumIx
            count = count + 1
        STDDEV = math.sqrt(sumIx / count)
        value = STDDEV / RMS

        d = {'channel': channel, 'value': value}

        return d




if __name__ == '__main__':
    batch = True
    '''If batch it true provide track name.  If not batch provide track name as empty string'''
    trackName = 'Charlotte Speedway'

    metricCreator = metricCreator()
    root = tk.Tk()
    root.withdraw()
    simFilePathDirectory = filedialog.askdirectory(title="Select Parent Directory That SIM Folders are Located in")
    dir_list = os.listdir(simFilePathDirectory)
    try:
        dir_list.remove('RunConfig.xml')
        dir_list.remove('RunMatrix.csv')
    except:
        print('no extra files to remove')
    gripResults, metricResults = metricCreator.loopResults(simFilePathDirectory, dir_list, trackName)
    gripResultsDF = pd.DataFrame.from_records(gripResults)
    export_csv = gripResultsDF.to_csv('C:/GM Racing/SIM/Projects/Grip Metric/Test_Run_Calc_Validation/gripTest.csv',
                                      index=False, header=True)

    # export_csv = gripResultsDF.to_csv('C:/gripMetricsTest/gripTest.csv', index=False,
    #                                 header=True)

