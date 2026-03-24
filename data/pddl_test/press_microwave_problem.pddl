(define (problem press_microwave)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    microwave_1 - microwave
  )
  (:init
    (reachable robot microwave_1)
  )
  (:goal (powered_on microwave_1))
)