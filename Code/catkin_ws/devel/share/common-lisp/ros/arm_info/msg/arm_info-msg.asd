
(cl:in-package :asdf)

(defsystem "arm_info-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "joint_info" :depends-on ("_package_joint_info"))
    (:file "_package_joint_info" :depends-on ("_package"))
    (:file "pos_info" :depends-on ("_package_pos_info"))
    (:file "_package_pos_info" :depends-on ("_package"))
  ))