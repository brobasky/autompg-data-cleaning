import csv
import logging
import requests
import argparse
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="autompg3.log",
                    level=logging.DEBUG,
                    format=LOG_FORMAT,
                    filemode='w')
logger=logging.getLogger()
formatter=logging.Formatter('%(levelname)s :: %(name)s :: %(module)s :: %(message)s')
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.info('defines AutoMPG and AutoMPGData objects, instantiates AutoMPGData object from text file')


class AutoMPG:
    def __init__(self,make,model,year,mpg):
        self.make=make
        self.model=model
        self.year=year
        self.mpg=mpg
    def __repr__(self):
        return f'AutoMPG({self.make},{self.model},{self.year},{self.mpg})'

    def __str__(self):
        return f'make:{self.make}, model:{self.model}, year:{self.year}, mpg:{self.mpg}'

    def __eq__(self,other):
        if type(self) == type(other):
            return self.make==other.make and self.model==other.model and self.year==other.year and self.mpg==other.mpg
        else:
            return NotImplemented

    def __lt__(self,other):
        if type(self)==type(other):
            return ((self.make,self.model,self.year,self.mpg)<(other.make,other.model,other.year,other.mpg))
        else:
            return NotImplemented

    def __hash__(self):
        return hash((self.make,self.model,self.year,self.mpg))


class AutoMPGData:
    def __init__(self):
        self.data=[]
        self.yearly_averages={}
        self.averages_by_make={}
        self._load_data()

    def __iter__(self):
        return self

    def _get_data(self):
        response=requests.get('https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data')
        with open('./auto-mpg.data.txt','w') as f:
            f.write(response.text)
        self._clean_data()
        logger.debug('called by _clean_data except block in event of FileNotFoundError, gets data, writes to file and calls _clean_data again')

    def _clean_data(self):
        logger.debug('opens data file and clean data file')

        try:
            with open("auto-mpg.data.txt","r") as f, open("auto-mpg.clean.txt","w") as f2:
                lines=f.readlines()
                for line in lines:
                    cleanedline=line.expandtabs(1)
                    f2.write(cleanedline)
                logger.debug('iterates through and cleans lines')
        except FileNotFoundError:
            self._get_data()

    def _load_data(self):
        self._clean_data()
        with open("auto-mpg.clean.txt","r") as csvfile:
            logger.debug('opens csv file')
            csvreader= csv.reader(csvfile, delimiter=' ', skipinitialspace=True)
            logger.debug('creates csv reader object')
            for row in csvreader:
                makemodel=row[8]
                mmsplit=makemodel.split()
                ma=mmsplit[0]
                if ma == 'chevy' or ma == 'chevroelt':
                    ma='chevrolet'
                elif ma == 'maxda':
                    ma='mazda'
                elif ma=='mercedes-benz':
                    ma='mercedes'
                elif ma == 'toyouta':
                    ma='toyata'
                elif ma == 'vokswagen' or ma == 'vw':
                    ma='volkswagen'
                mod=' '.join(mmsplit[1:])
                yr=int(row[6])+1900
                MPG=float(row[0])
                self.data.append(AutoMPG(ma,mod,yr,MPG))
            logger.debug('iterates through csv reader,organises data, standardizes make attribute')

    def sort_by_default(self):
        self.data.sort()
        logger.debug('sorts data by default')


    def sort_by_year(self):
        self.data=sorted(self.data,key=lambda car: car.year)
        logger.debug('sorts data by year')

    def sort_by_mpg(self):
        self.data=sorted(self.data,key=lambda car: car.mpg)
        logger.debug('sorts by mpg')

    def mpg_by_year(self):
        yearly_data= defaultdict(list)
        yearly_averages= defaultdict(float)
        for car in self.data:
            yearly_data[car.year].append(car.mpg)
        for key in yearly_data:
            yearly_averages[key]=(sum(yearly_data[key])/len(yearly_data[key]))
        self.yearly_averages=yearly_averages
        logger.debug('creates defaultdict with average mpg per year, edits yearly_averages attribute')

    def mpg_by_make(self):
        data_by_make=defaultdict(list)
        averages_by_make=defaultdict(float)
        for car in self.data:
            data_by_make[car.make].append(car.mpg)
        for key in data_by_make:
            averages_by_make[key]=(sum(data_by_make[key])/len(data_by_make[key]))
        self.averages_by_make=averages_by_make
        logger.debug('creates defaultdict with average mpg by make, edits mpg_by_make attribute')

def main():
    logger.debug('main function instantiates AutoMPGData object and argparser')
    MPGData=AutoMPGData()
    parser=argparse.ArgumentParser()
    parser.add_argument('command', metavar='<command>', type=str)
    parser.add_argument("-s","--sort",choices=['default','year','mpg'])
    parser.add_argument("-o","--ofile", nargs='?', type=str)
    parser.add_argument("-p","--plot", nargs='?')
    args=parser.parse_args()
    logger.debug('instantes parser object, configures possible command line arguments and calls parse_args method')


    if args.command=='print':
        if args.sort == 'default':
            MPGData.sort_by_default()
        elif args.sort == 'year':
            MPGData.sort_by_year()
        elif args.sort == 'mpg':
            MPGData.sort_by_mpg()
        logger.debug('calls appropriate sorting method of AutoMPGData object based on command line arguments')
        for car in MPGData.data:
            print(car)
        logger.debug('excecutes print command')
    elif args.command=='mpg_by_year':
        MPGData.mpg_by_year()
        print(MPGData.yearly_averages)
        logger.debug('excecutes mpg_by_year command')
    elif args.command=='mpg_by_make':
        MPGData.mpg_by_make()
        print(MPGData.averages_by_make)
        logger.debug('excecutes mpg_by_make command')

    if '-o' in sys.argv or '--ofile' in sys.argv:
        try:
            with open(args.ofile,'w') as outfile:
                if args.command=='print':
                    for car in MPGData.data:
                        outfile.write(f'{car.make},{car.model},{car.year},{car.mpg}\n')
                elif args.command=='mpg_by_year':
                    for key in MPGData.yearly_averages:
                        outfile.write(f'{key},{MPGData.yearly_averages[key]}\n')
                elif args.command=='mpg_by_make':
                    for key in MPGData.averages_by_make:
                        outfile.write(f'{key},{MPGData.averages_by_make[key]}\n')
            logger.debug('writes data requested by command to a specified output file')
        except TypeError:
            for car in MPGData.data:
                sys.stdout.write(f'{car.make},{car.model},{car.year},{car.mpg}\n')
            logger.debug('writes data to stdout')
    else:
        pass

    if '-p' in sys.argv or '--plot' in sys.argv:
        if args.command=='mpg_by_year':
            years=list(MPGData.yearly_averages.keys())
            averages=list(MPGData.yearly_averages.values())
            plt.plot(years,averages,'--r')
            plt.show()
            logger.debug('calls show method')
        elif args.command=='mpg_by_make':
            makes=list(MPGData.averages_by_make.keys())
            averages=list(MPGData.averages_by_make.values())
            plt.plot([makes,averages,'--r'])
            plt.savefig('mpg3.pdf')



if __name__ == '__main__':
    main()
