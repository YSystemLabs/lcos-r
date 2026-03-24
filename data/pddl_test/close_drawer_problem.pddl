(define (problem close_drawer)
  (:domain lcos-r-domestic)
  (:objects
    robot - agent
    drawer_1 - drawer
  )
  (:init
    (reachable robot drawer_1)
    (open drawer_1)
  )
  (:goal (closed drawer_1))
)