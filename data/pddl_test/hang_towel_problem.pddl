(define (problem hang_towel)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    hook_1 - object
    towel_1 - towel
  )
  (:init
    (holding robot towel_1)
  )
  (:goal (hung towel_1))
)