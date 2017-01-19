# -*- mode: python -*-

block_cipher = None


a = Analysis(['nmrml2isa_cli.py'],
             pathex=['..\\..\\nmrml2isa', '..\\..\\.', 'C:\Python35\Lib\site-packages\pronto'],
             binaries=None,
             datas= [ ('..\\..\\nmrml2isa\\default\\a_nmrML.txt', 'nmrml2isa\\default' ),
		              ('..\\..\\nmrml2isa\\default\\i_nmrML.txt', 'nmrml2isa\\default' ),
		              ('..\\..\\nmrml2isa\\default\\s_nmrML.txt', 'nmrml2isa\\default' ),
		              ('..\\..\\nmrml2isa\\nmrCV.owl', 'nmrml2isa')
		              ],
             hiddenimports=['pronto'],
             hookspath=['.'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='nmrml2isa_cli',
          debug=False,
          strip=False,
          upx=True,
          console=True )
