from gymnasium.envs.registration import register

register(
    id="lean_gym/LeanEnvREPL-v0",
    entry_point="lean_gym.envs:LeanEnvREPL",
)
