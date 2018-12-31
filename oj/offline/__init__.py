'Offline Judge'


import argparse
import csv
import os
import pprint
import shutil
import subprocess
import sys
import threading



class Thread(threading.Thread):
    'Subclass of threading.Thread with return value'
    return_value = None
    def run(self):
        try:
            if self._target:
                self.return_value = self._target(*self._args, **self._kwargs)
        finally:
            del self._target, self._args, self._kwargs


def judge(examinee, problem, cases, args):
    'Thread'
    result = []
    try:
        open(os.path.join(args.path, 'source codes', examinee, problem, problem + '.cpp'))
    except FileNotFoundError:
        return ['SFNF (source file not found)'] * cases
    subprocess.run([args.cpp,
                    os.path.join(args.path, 'source codes', examinee, problem, problem + '.cpp'),
                    '-o', os.path.join(args.path, 'source codes', examinee, problem, problem)],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        open(os.path.join(args.path, 'source codes', examinee, problem, problem), 'rb')
    except FileNotFoundError:
        return ['CE (compilation error)'] * cases
    for i in range(1, cases + 1):
        shutil.copyfile(os.path.join(args.path, 'test cases', problem, problem + str(i) + '.in'),
                        problem + '.in')
        try:
            subprocess.run(os.path.join(args.path, 'source codes', examinee, problem, problem),
                           timeout=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            try:
                if (open(problem + '.out').read().rstrip() ==
                        open(os.path.join(args.path, 'test cases', problem,
                                          problem + str(i) + '.out')).read().rstrip()):
                    result.append('AC (accepted)')
                else:
                    result.append('WA (wrong answer)')
                # os.remove(problem + '.out')
            except FileNotFoundError:
                result.append('OFNF (output file not found)')
        except (subprocess.TimeoutExpired, ValueError):
            result.append('TLE (time limit exceeded)')
        except subprocess.CalledProcessError:
            result.append('RE (runtime error)')
        finally:
            try:
                os.remove(problem + '.out')
            except FileNotFoundError:
                pass
            os.remove(problem + '.in')
    os.remove(os.path.join(args.path, 'source codes', examinee, problem, problem))
    return result


def main(args):
    "__name__ == '__main__'"
    print(args.path)
    print(args.output)
    try:
        file = open(args.output, 'w', newline='')
    except TypeError:
        file = sys.stdout
    # print(file)
    print(args.pas, args.c, args.cpp)
    problems = os.listdir(os.path.join(args.path, 'test cases'))
    problems.sort()
    # pprint.pprint(problems)
    cases = {}
    for problem in problems:
        cases[problem] = len(os.listdir(os.path.join(args.path, 'test cases', problem))) // 2
    pprint.pprint(cases)
    fieldnames = ['']
    for problem in problems:
        for i in range(1, cases[problem] + 1):
            fieldnames.append(problem + str(i))
        fieldnames.append(problem)
    fieldnames.append('Total')
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    # file.write(','.join(fieldnames) + '\n')
    examinees = os.listdir(os.path.join(args.path, 'source codes'))
    examinees.sort()
    pprint.pprint(examinees)
    for examinee in examinees:
        threads = []
        for problem in problems:
            threads.append(Thread(target=judge, args=(examinee, problem, cases[problem], args)))
            threads[-1].start()
        score = 0
        result = [examinee]
        for thread in threads:
            thread.join()
            # pprint.pprint(thread.return_value)
            score += thread.return_value.count('AC (accepted)') * 100 / len(thread.return_value)
            result += thread.return_value + [thread.return_value.count('AC (accepted)')
                                             * 100 / len(thread.return_value)]
        result.append(score)
        # pprint.pprint(result)
        # file.write(','.join(result) + '\n')
        # pprint.pprint(dict(zip(fieldnames, result)))
        writer.writerow(dict(zip(fieldnames, result)))
        file.flush()
    file.close()


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('path', nargs='?', const=1, default='.',
                        help='Directory (the current directory by default)')
    PARSER.add_argument('-o', '--output',
                        help='Write output to <file> (default to stdout)', metavar='<file>')
    PARSER.add_argument('--pas', default='fpc', help='Pascal Compiler', metavar='<fpc>')
    PARSER.add_argument('--c', default='gcc', help='C Compiler', metavar='<gcc>')
    PARSER.add_argument('--cpp', default='g++', help='C++ Compiler', metavar='<g++>')
    main(PARSER.parse_args())
