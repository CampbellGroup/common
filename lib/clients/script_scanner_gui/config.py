class config(object):

    #list in the format (import_path, class_name)
    scripts = [('Qsim.scripts.experiments.tickle.tickle_experiment', 'ticklescan'),
               ('Qsim.scripts.experiments.wavemeter_linescan_369.wavemeter_linescan_369', 'wavemeter_linescan_369'),
               ('Qsim.scripts.experiments.wavemeter_linescan_935.wavemeter_linescan_935', 'wavemeter_linescan_935')
               ]

    allowed_concurrent = {
    }
    
    launch_history = 1000   