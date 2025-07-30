Getting infrastructure_config onto the new machine.


SCP with Setup in One Command                                                  
                                                                                           
  # From your machine TO the new machine                                                   
  scp ~/claude-configs/claude-v2-config.txt                                                
  username@new-machine:~/claude-v2-config.txt                                              

  # Then on the new machine
  ./setup_clap_deployment.sh --config-file ~/claude-v2-config.txt

