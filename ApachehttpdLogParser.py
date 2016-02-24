#!/usr/bin/env python
#!/usr/bin/python -tt

import sys
import argparse
import re
import time
from collections import Counter
import logging

# Configure your logging configuration 
logging.basicConfig(level=logging.DEBUG,
                    stream=sys.stdout,
                    format='%(name)s %(funcName)s:%(lineno)s %(message)s')

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

log_file_pattern = re.compile(r'''(?P<remote_host>\S+) #host ip-address
                             \s+ #whitespace
                             \S+ # dash
                             \s+ #whitespace
                             \S+ # dash
                             \s+ #whitespace
                             (?P<datetime>\[[^\[\]]+\]) #datetime
                             \s+ #whitespace
                             (?P<request>"[^"]+") #request proto
                             \s+ #whitespace
                             (?P<status>\d+) #status
                             \s+ #whitespace
                             (?P<bytes>-|\d+) #bytes
                             ''', re.VERBOSE)


''' Apache httpd logs parser class '''

class ApachehttpdLogParser:

    @property
    def logger(self):
        name = '.'.join([__name__, self.__class__.__name__])
        return logging.getLogger(name)

    def __init__(self, args):
        # Check for valid input file

        self.input_log_file = args.input_logfile_name
        try:
            self.input_file = open(self.input_log_file, 'r')
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            print 'Cannot open Log filename:', self.input_log_file
            print "Specify a Valid Log filename to parse"
            sys.exit(1)

        if args.outputfile:
            try:
                self.output_file = open(args.outputfile, 'w')
            except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                print 'Cannot open output Log filename:', self.output_file
                print "Specify a Valid Log filename to parse"
                sys.exit(1)
            sys.stdout = self.output_file

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.input_file.close()
        self.output_file.close()

    @staticmethod
    def isunsuccessfulpage(logline):
        # all failures and redirects.
        logline["status"] = int(logline["status"])
        if logline["status"] < 200 or logline["status"] >= 300:
            if logline["status"] == 404:
                return False

        # successful page
        return True

    @staticmethod
    def issuccessfulpage(logline):
        # Failures and redirects.
        logline["status"] = int(logline["status"])
        if logline["status"] < 200 or logline["status"] >= 300:
            return False

        # successful page
        return True

    @staticmethod
    def generate_groupdict(loglines):
        for line in loglines:
           match= log_file_pattern.match(line)
           if match:
              yield match.groupdict()

    def get_top10_requests(self):
        pages = []

        #self.logger.debug('get_top10_requests(): %s:', self.output_file)
        #logging.debug('%s: ', self.input_file)
        # Check current position
        position = self.input_file.tell()
        #print "Current file position : ", position

        #self.logger.debug('Current file position : %d', position)

        # Reposition pointer at the beginning once again
        position = self.input_file.seek(0, 0)
        #print "Current file position after reset: ", position

        #self.logger.debug('Current file position after reset:%d', position)

        ''' read all logfile lines and generatea a groupdictinary '''
        logfile_lines = self.input_file.readlines()
        mgroupdict = self.generate_groupdict(logfile_lines)

        #start = time.clock()
        if mgroupdict:
          for line in mgroupdict:
            if self.issuccessfulpage(line):
              pages.append(line)
            else:
              continue
        #print time.clock() - start

        # show top10 requests and their total
        pageViews = Counter(x['request'] for x in pages)
        top10 = pageViews.most_common(10)

        print " \nTOP 10 REQUESTS"
        print "Number of Times       vs     Requested page"
        for letter, count in top10:
            print "  %5d      %s" % (count, letter)

        print "  %5d " % len(pages)

        # Check current position
        position = self.input_file.tell()
        #print "Current file position : ", position
        #self.logger.debug('Current file position :: %d', position)

    def get_percentage_successful_requests(self):
        sucpages = []
        totalpages = []

        # Reposition file pointer at the beginning again
        position = self.input_file.seek(0, 0)
        # print "Current file position after reset: ", position
        #self.logger.debug('Current file position after reset:: %d:', position)

        ''' read all logfile lines and generatea a groupdictinary '''
        logfile_lines = self.input_file.readlines()
        mgroupdict = self.generate_groupdict(logfile_lines)

        if mgroupdict:
          for line in mgroupdict:
            if self.issuccessfulpage(line):
               sucpages.append(line)
            else:
               totalpages.append(line)
               continue

        # show top10 requests and their total
        pageViews = Counter(y['request'] for y in totalpages)
        pageViews = Counter(x['request'] for x in sucpages)
        total = len(sucpages) + len(totalpages)

        if total:
            per_suc_requests = 100 * len(sucpages) / float(total)
            print " \nPERCENTAGE OF SUCCESSFUL REQUESTS"
            print "  %5f " % abs(per_suc_requests)
        elif total == 0:
            print " \nTOTAL SUCCESSFUL REQUESTS is ZERO"

    def get_percentage_unsuccessful_requests(self):
        unsucpages = []
        totalpages = []

        # Reposition pointer at the beginning once again
        position = self.input_file.seek(0, 0)
        #self.logger.debug('Current file position after reset:: %d:', position)

        ''' read all logfile lines and generatea a groupdictinary '''
        logfile_lines = self.input_file.readlines()
        mgroupdict = self.generate_groupdict(logfile_lines)

        if mgroupdict:
          for line in mgroupdict:
            if self.isunsuccessfulpage(line):
               unsucpages.append(line)
            else:
               totalpages.append(line)
               continue

        # show top10 requests and their total
        totalpageViews = Counter(y['request'] for y in totalpages)
        pageViews = Counter(x['request'] for x in unsucpages)
        total = len(unsucpages) + len(totalpages)
        if total:
            per_unsuc_requests = 100 * len(unsucpages) / float(total)
            print " \nPERCENTAGE OF UNSUCCESSFUL REQUESTS"
            print "  %5f " % abs(per_unsuc_requests)
        elif total == 0:
            print " \nTOTAL UNSUCCESSFUL REQUESTS is ZERO"

    def get_top10_unsuccessful_requests(self):
        pages = []

        # Reposition pointer at the beginning once again
        position = self.input_file.seek(0, 0)
        #self.logger.debug('Current file position after reset:: %d:', position)

        ''' read all logfile lines and generatea a groupdictinary '''
        logfile_lines = self.input_file.readlines()
        mgroupdict = self.generate_groupdict(logfile_lines)

        if mgroupdict:
          for line in mgroupdict:
            if self.isunsuccessfulpage(line):
               pages.append(line)
            else:
               continue

        # show top10 unsuccesful requests and their total
        pageViews = Counter(x['request'] for x in pages)
        unsuccesstop10 = pageViews.most_common(10)

        print " \nTOP 10 UNSUCCESSFUL REQUESTS"
        print "Number of Times       vs     Requested page"
        for letter, count in unsuccesstop10:
            print "  %5d      %s" % (count, letter)

        print "  %5d Total" % len(pages)

    def get_top10_ip_requests(self):
        pages = []

        # Reposition pointer at the beginning once again
        position = self.input_file.seek(0, 0)
        # print "Current file position after reset: ", position
        #self.logger.debug('Current file position after reset:: %d:', position)

        ''' read all logfile lines and generatea a groupdictinary '''
        logfile_lines = self.input_file.readlines()
        mgroupdict = self.generate_groupdict(logfile_lines)

        if mgroupdict:
          for line in mgroupdict:
            if self.issuccessfulpage(line):
               pages.append(line)
            else:
               continue

        # show top10 requests and their total
        pageViews = Counter(x['remote_host'] for x in pages)
        iptop10 = pageViews.most_common(10)

        print " \nTOP 10 IP REQUESTS"
        print "Number of Times       vs     Requested page"
        for letter, count in iptop10:
            print "  %5d      %s" % (count, letter)


def get_args():
    '''This function parses input args and return argument values'''

    description = 'This script parses user provided <input_log_filename> apache httpd log file \
		 and displays log file statistics. Also user can provide optional arguments'

    argparser = argparse.ArgumentParser(prog="ApachehttpdLogParser",
                                        description=description)
    #parser.add_argument('-i','--logfile', help='Input file name',required=True)
    argparser.add_argument(
        'input_logfile_name', help='Give input log file name')
    argparser.add_argument(
        '-o', '--outputfile', help='Give output file name', required=False)
    argparser.add_argument(
        '-r', '--htmlfile', help='html file report', required=False)
    argparser.add_argument(
        '-A', '--TOP10REQUESTS', help='PRINT TOP 10 REQUESTS', action='store_true')
    argparser.add_argument('-B', '--PERSUCESSFULREQUESTS',
                           help='PRINTS PERCENTAGE OF SUCCESSSFUL REQUESTS', action='store_true')
    argparser.add_argument('-C', '--PERUNSUCESSFULREQUESTS',
                           help='PRINTS PERCENTAGE OF UNSUCCESSSFUL REQUESTS', action='store_true')
    argparser.add_argument('-D', '--TOP10UNSUCCESSFULREQUESTS',
                           help='PRINTS TOP 10 UNSUCCESFUL REQUESTS', action='store_true')
    argparser.add_argument(
        '-E', '--TOP10IPREQUESTS', help='PRINTS TOP 10 IP REQUESTS', action='store_true')

    args = argparser.parse_args()

    # Return all arg variable values
    return args

def main():

    from time import time
    args = get_args()

    starttime = time()
    logparser = ApachehttpdLogParser(args)

    if args.TOP10REQUESTS:
        logparser.get_top10_requests()
    elif args.PERSUCESSFULREQUESTS:
        logparser.get_percentage_successful_requests()
    elif args.PERUNSUCESSFULREQUESTS:
        logparser.get_percentage_unsuccessful_requests()
    elif args.TOP10UNSUCCESSFULREQUESTS:
        logparser.get_top10_unsuccessful_requests()
    elif args.TOP10IPREQUESTS:
        logparser.get_top10_ip_requests()
    else:
        logparser.get_top10_requests()
        logparser.get_percentage_successful_requests()
        logparser.get_percentage_unsuccessful_requests()
        logparser.get_top10_unsuccessful_requests()
        logparser.get_top10_ip_requests()

    endtime = time()
    runtime = endtime - starttime

    #print 'Run proceeded for %.2f seconds' % (runtime)
    logging.debug('Run proceeded for %.2f seconds', runtime)

if __name__ == "__main__":
    main()
