"""
    submit `main.py` on HTCondor, splitting the production into one job per sample
"""
import os, sys
import argparse
import datetime
# custom imports
import data_toolkit as data
import utils

CMSSW_BASE = os.environ.get('CMSSW_BASE')
THISDIR    = os.path.dirname(os.path.abspath(__file__))


def parse_arguments():

    defaults_ = {
        "channels": ['emu'],
        "queue": "tomorrow",
        "tag": None,
    }

    parser = argparse.ArgumentParser(
        description="Submit corrections/main.py on HTCondor, one job per sample",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--input", "-i",
                        required=True,
                        help=".yml file containing the input ntuples locations and metadata (forwarded to main.py)"
                        )
    parser.add_argument("--outdirectory", "-o",
                        default=None,
                        help="directory for output-ntuples. N.B. overwrites the location in the input .yml file if provided."
                        )
    parser.add_argument('--channels',
                        nargs='+',
                        default=defaults_["channels"],
                        help='select channels to process.')
    parser.add_argument('--mc_only',
                        action='store_true',
                        help='process only MC samples (no data).'
                        )
    parser.add_argument('--test_samples',
                        action='store_true',
                        help='Run only on signal and ttbar samples for quick testing'
                        )
    parser.add_argument('-N', '--Nevents',
                        type=int, default=None,
                        help='MAX number of events to process. None: all events.'
                        )
    parser.add_argument('--tag',
                        default=defaults_["tag"],
                        help='tag used in the Farm directory name.'
                        )
    parser.add_argument('--queue',
                        default=defaults_["queue"],
                        help='HTCondor +JobFlavour (espresso, microcentury, longlunch, workday, tomorrow, testmatch, nextweek).'
                        )
    parser.add_argument('--submit',
                        action='store_true',
                        help='submit the jobs to HTCondor (default: dry-run, only create the Farm directory).'
                        )
    return parser.parse_args()


def samples_for_channel(ch, test_samples, mc_only):
    """ return the list of (sample_name, is_data) to process for one channel """

    mc_names = data.samples.mc_samples_names
    if test_samples:
        mc_names = ['tt_fullylep', 'tt_semilep', 'tt_had', 'bstautau', 'bstautauext']

    samples_ = [(name, False) for name in mc_names]
    if not (mc_only or test_samples):
        samples_ += [(name, True) for name in data.samples.data_samples_names.get(ch, [])]

    return samples_


def build_condor_job(args, FarmDirectory, ch, sample_name):
    """ build the worker script and condor submission file to run main.py on a single sample """

    jobname = f"{sample_name}_{ch}"

    # main.py only enables ROOT implicit-MT when running on >10k events (see setup_multithreading());
    # request enough CPUs for the job's cgroup to let TBB actually use multiple threads in that case.
    request_cpus = 4 if (args.Nevents is None or args.Nevents > 10000) else 1

    cmd_parts = ["python3", "main.py", "--input", args.input, "--channels", ch, "--sample", sample_name]
    if args.outdirectory:
        cmd_parts += ["--outdirectory", args.outdirectory]
    if args.Nevents:
        cmd_parts += ["-N", str(args.Nevents)]
    cmd = " ".join(cmd_parts)

    # ---- worker script to execute -----
    worker_path = os.path.join(FarmDirectory, f"worker_{jobname}.sh")
    with open(worker_path, 'w') as worker:
        worker.write(f'''#!/bin/bash
echo ------- START JOB :  `date`
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd {CMSSW_BASE}/src
eval `scram r -sh`
cd {CMSSW_BASE}/src/bstautau-analyzer/
pip3 install -e .
cd {THISDIR}

echo "INFO: run corrections on sample {sample_name} ({ch})"
echo "{cmd}"
{cmd}

echo ------- END JOB :  `date`
''')
    os.system(f'chmod u+x {worker_path}')

    # ---- condor submission file -----
    condor_path = os.path.join(FarmDirectory, f"condorsub_{jobname}.sub")
    with open(condor_path, 'w') as condor:
        condor.write(f'''
executable = {worker_path}

output     = {FarmDirectory}/output/{jobname}.out
error      = {FarmDirectory}/output/{jobname}.err
log        = {FarmDirectory}/log/{jobname}.log

should_transfer_files = YES
when_to_transfer_output = ON_EXIT_OR_EVICT
use_x509userproxy = true
request_cpus = {request_cpus}

+JobBatchName = "{jobname}"
+JobFlavour = "{args.queue}"
+AccountingGroup = "group_u_CMST3.all"
+SingularityImage = "/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el8:x86_64"

queue 1
''')

    return condor_path


if __name__ == "__main__":

    if not CMSSW_BASE:
        utils.logger.print_error("CMSSW environment not set. Run `cmsenv` first.")
        sys.exit(1)

    args = parse_arguments()

    # input .yaml
    if not os.path.isfile(args.input):
        utils.logger.print_error(f"input file {args.input} does not exist.")
        sys.exit(1)
    args.input = os.path.abspath(args.input)
    # output directory
    if args.outdirectory:
        args.outdirectory = os.path.abspath(args.outdirectory)
        utils.logger.print_info(f"Output directory overridden to: {args.outdirectory}")

    jobtag = '_'.join(filter(None, [args.tag, datetime.datetime.now().strftime('%Y%m%d-%H%M%S')]))
    FarmDirectory = os.path.join(THISDIR, f"jobLogs_corrections_{jobtag}")
    os.makedirs(os.path.join(FarmDirectory, 'output'), exist_ok=True)
    os.makedirs(os.path.join(FarmDirectory, 'log'), exist_ok=True)
    utils.logger.print_info(f"Created farm directory: {FarmDirectory}")

    condorfiles = []
    for ch in args.channels:
        utils.logger.print_bold(f"\n--------- CHANNEL {ch} ---------")
        for sample_name, is_data in samples_for_channel(ch, args.test_samples, args.mc_only):
            utils.logger.print_addition(f"{sample_name} ({'data' if is_data else 'MC'})")
            condor_path = build_condor_job(args, FarmDirectory, ch, sample_name)
            condorfiles.append(condor_path)

    print("--"*20+"\n")
    utils.logger.print_success(f"prepared {len(condorfiles)} condor jobs")

    # submitter script to submit all the jobs
    submitter_path = os.path.join(FarmDirectory, 'submitter.sh')
    with open(submitter_path, 'w') as submitter:
        submitter.write('#!/bin/bash\n')
        for condor_script in condorfiles:
            utils.logger.print_exe(f"condor_submit {condor_script}", logger=submitter)
        submitter.write('echo "DONE | all jobs submitted"\n')
    os.system(f'chmod u+x {submitter_path}')

    if not args.submit:
        utils.logger.print_info(f"DRYRUN: to submit the jobs, run: {submitter_path}")
    else:
        utils.logger.print_info(f"Submitting the jobs with: {submitter_path}")
        os.system(submitter_path)
