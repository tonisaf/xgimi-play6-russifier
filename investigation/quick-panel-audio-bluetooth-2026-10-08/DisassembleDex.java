import java.nio.file.*;
import java.io.File;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile;
import com.android.tools.smali.baksmali.Baksmali;
import com.android.tools.smali.baksmali.BaksmaliOptions;
public class DisassembleDex {
    public static void main(String[] args) throws Exception {
        BaksmaliOptions options = new BaksmaliOptions();
        options.localsDirective = true;
        options.parameterRegisters = true;
        options.debugInfo = true;
        Baksmali.disassembleDexFile(new DexBackedDexFile(new Opcodes(30, -1), Files.readAllBytes(Path.of(args[0])), 0), new File(args[1]), 4, options);
    }
}
