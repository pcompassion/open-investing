((nil .
      ((eval .
             (progn
               (setq ek/subproject-root (locate-dominating-file default-directory ".git"))
               (setq-local projectile-project-root
                                 (locate-dominating-file (file-name-parent-directory ek/subproject-root) ".git")
                                 ))
             )))
 )
